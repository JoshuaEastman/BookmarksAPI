import pytest
from model_bakery import baker

SUBMIT_URL = '/bookmarks/v1/bookmarks/submit/'

@pytest.mark.django_db
def test_submit_returns_201_and_pending_tag_feedback(api_client):
    '''
    POST /submit/ created an unapproved bookmark and returns:
        - tags (known)
        - pending_tags (unknown)
        - is_approved=False
    '''
    baker.make('bookmarks.Tag', slug='django', name='Django')
    payload = {
        'title': 'Django Docs',
        'url': 'https://docs.djangoproject.com',
        'description': 'Docs',
        'tags': ['django', 'api'], # api is unknown => pending
        'website': ''
    }

    r = api_client.post(SUBMIT_URL, data=payload, format='json')
    assert r.status_code == 201, r.content
    data = r.json()

    assert data['is_approved'] is False
    assert data['tags'] == ['django']
    assert data['pending_tags'] == ['api']
    assert 'created_at' in data

@pytest.mark.django_db
def test_submit_records_submitted_ip(api_client):
    '''
    Server should record client IP (fallback to REMOTE_ADDR in tests).
    '''
    payload = {
        'title': 'Site',
        'url': 'https://site.example',
        'description': 'Site description',
        'tags': ['django'],
        'website': ''
    }
    r = api_client.post(SUBMIT_URL, data=payload, format='json')
    assert r.status_code == 201
    data = r.json()

    from bookmarks.models import Bookmark
    obj = Bookmark.objects.get(id=data['id'])
    assert obj.submitted_ip in {'127.0.0.1', '::1'}