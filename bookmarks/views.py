import math, time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework import status, permissions
from .models import Bookmark, Tag
from .serializers import BookmarkReadSerializer, BookmarkSubmissionSerializer, BookmarkWriteSerializer
from .throttling import BookmarksReadsThrottle, BookmarksSubmitBurst, BookmarksSubmitDay

# Helpers
def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

class RateLimitHeadersMixin:
    '''
    Adds X-RateLimit-* headers based on DRF throttles.
    For multiple throttles, chooses the most restrictive (lowest remaining; tie-breaker: earliest reset)
    '''
    def _compute_throttle_state(self, request):
        now = time.time()
        best = None # tuple (remaining, resets_secs, limit)

        # Use the declared throttle_classes
        for ThrottleClass in getattr(self, 'throttle_classes', []):
            t = ThrottleClass()
            rate = t.get_rate()
            if not rate:
                continue

            # Parse rate
            try:
                num, duration = t.parse_rate(rate)
            except Exception:
                continue

            # Determine cache key for this request/view
            key = t.get_cache_key(request, self)
            if not key:
                continue

            history= t.cache.get(key, [])
            window_start = now - duration
            history = [ts for ts in history if ts > window_start]
            remaining = max(0, num - len(history))

            if history:
                oldest = history[0]
                reset_at = int(math.ceil(oldest + duration)) # epoch when reset happens
            else:
                reset_at = int(math.ceil(now + duration))

            cur = (remaining, reset_at, num)

            if best is None:
                best = cur
            else:
                if cur[0] < best[0] or (cur[0] == best[0] and cur[1] < best[1]):
                    best = cur

        return best # or None

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        state = self._compute_throttle_state(request)
        if state is not None:
            remaining, reset_at, limit = state
            try:
                response["X-RateLimit-Limit"] = str(limit)
                response["X-RateLimit-Remaining"] = str(remaining)
                response["X-RateLimit-Reset"] = str(reset_at)
            except Exception:
                pass

        return response


# Create your views here.
class HealthCheckView(RateLimitHeadersMixin, APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, *args, **kwargs):
        content = {'status': 'ok'}
        return Response(content, status.HTTP_200_OK)

class BookmarkListView(RateLimitHeadersMixin, ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BookmarkReadSerializer
    throttle_classes = [BookmarksReadsThrottle]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        # Get queryset; prefetch related tags (approved Bookmarks)
        qs = Bookmark.objects.filter(is_approved=True).prefetch_related('tags')

        # Get tag param from request
        tag = self.request.query_params.get('tag')

        # If tag, filter queryset by tag
        if tag:
            qs = qs.filter(tags__slug=tag)
        return qs

class BookmarkDetailView(RateLimitHeadersMixin, RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BookmarkReadSerializer
    throttle_classes = [BookmarksReadsThrottle]
    lookup_url_kwarg = 'id' # match /v1/bookmarks/<int:id>/
    queryset = Bookmark.objects.filter(is_approved=True).prefetch_related('tags')

class BookmarkSubmitView(RateLimitHeadersMixin, CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BookmarkWriteSerializer
    throttle_classes = [BookmarksSubmitDay, BookmarksSubmitBurst]

    def create(self, request, *args, **kwargs):
        # validate input
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save with client IP (serializer default is_approved=False)
        ip = _client_ip(request)
        instance = serializer.save(submitted_ip=ip)

        # return submission reciept
        out = BookmarkSubmissionSerializer(instance, context = self.get_serializer_context())
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)
