import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from model_bakery import baker


def _add_session_and_messages(request):
    """Attach a working session and messages storage to a RequestFactory request."""
    # Add session
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()
    # Add messages
    setattr(request, "_messages", FallbackStorage(request))
    return request


@pytest.mark.django_db
def test_admin_approve_selected_sets_fields():
    """
    Admin bulk action should:
      - set is_approved=True
      - stamp approved_at
      - set approved_by to the admin user
      - add a success message (requires messages/session on request)
    """
    from bookmarks.admin import BookmarkAdmin
    from bookmarks.models import Bookmark

    # Admin user acting as moderator
    User = get_user_model()
    admin_user = User.objects.create_user(
        username="admin", password="x", is_staff=True, is_superuser=True
    )

    # Two unapproved bookmarks to approve
    b1 = baker.make("bookmarks.Bookmark", is_approved=False)
    b2 = baker.make("bookmarks.Bookmark", is_approved=False)

    # Build a real HttpRequest with session + messages
    rf = RequestFactory()
    request = rf.post("/")  # method doesn't matter for calling the action directly
    request.user = admin_user
    _add_session_and_messages(request)

    # Execute admin action on a queryset
    ma = BookmarkAdmin(Bookmark, AdminSite())
    qs = Bookmark.objects.filter(id__in=[b1.id, b2.id])
    ma.approve_selected(request, qs)

    # Assertions
    b1.refresh_from_db()
    b2.refresh_from_db()
    assert b1.is_approved is True and b2.is_approved is True
    assert b1.approved_by_id == admin_user.id and b2.approved_by_id == admin_user.id
    assert b1.approved_at is not None and b2.approved_at is not None
