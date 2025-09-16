from rest_framework.throttling import SimpleRateThrottle

class _IPRateThrottle(SimpleRateThrottle):
    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        if not ident:
            return None
        return self.cache_format % {'scope': self.scope, 'ident': ident}

class BookmarksReadsThrottle(_IPRateThrottle):
    scope = 'bookmarks_reads'

class BookmarksSubmitBurst(_IPRateThrottle):
    scope = 'bookmarks_submit_burst'

class BookmarksSubmitDay(_IPRateThrottle):
    scope = 'bookmarks_submit_day'
