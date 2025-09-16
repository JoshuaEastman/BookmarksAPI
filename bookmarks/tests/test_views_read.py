import pytest
from django.utils import timezone
from datetime import timedelta
from model_bakery import baker

LIST_URL = '/bookmarks/v1/bookmarks/'

@pytest.mark.django_db
def test_list_returns_approved_only(api_client):
    '''
    Public list should return only approved bookmarks.
    '''
    t = baker.make('bookmarks.Tag', slug='django')
    baker.make('bookmarks.Bookmark', title='Approved 1', is_approved=True, tags=[t])
    baker.make('bookmarks.Bookmark', title='Unapproved 1', is_approved=False)

    r = api_client.get(LIST_URL)
    assert r.status_code == 200
    titles = [b['title'] for b in r.json().get('results', [])]
    assert 'Approved 1' in titles
    assert 'Unapproved 1' not in titles

@pytest.mark.django_db
def test_list_filters_by_tag(api_client):
    '''
    ?tag=<slug> filter by tag slug
    '''

    t_dj = baker.make('bookmarks.Tag', slug='django')
    t_api = baker.make('bookmarks.Tag', slug='api')
    baker.make('bookmarks.Bookmark', title='Django Site', is_approved=True, tags=[t_dj])
    baker.make('bookmarks.Bookmark', title='API Site', is_approved=True, tags=[t_api])

    r = api_client.get(LIST_URL, {'tag': 'django'})
    assert r.status_code == 200
    titles = [b['title'] for b in r.json().get('results', [])]
    assert titles == ['Django Site']

@pytest.mark.django_db
def test_list_supports_search(api_client):
    '''
    ?search= matches title/url/description/domain/tags (per view config)
    '''
    baker.make('bookmarks.Bookmark', title='Learn Django', description='Web framework', is_approved=True)
    baker.make('bookmarks.Bookmark', title='Other', description='something else', is_approved=True)
    r = api_client.get(LIST_URL, {'search': 'django'})
    assert r.status_code == 200
    titles = [b['title'] for b in r.json().get('results', [])]
    assert titles == ['Learn Django']

@pytest.mark.django_db
def test_list_supports_ordering_created_at(api_client):
    '''
    ?ordering=created_at / -created_at.
    '''
    older = baker.make('bookmarks.Bookmark', title='Older', is_approved=True, created_at=timezone.now() - timedelta(days=2))
    newer = baker.make('bookmarks.Bookmark', title='Newer', is_approved=True, created_at=timezone.now())

    r = api_client.get(LIST_URL, {'ordering': '-created_at'})
    assert r.status_code == 200
    got = [b['title'] for b in r.json().get('results', [])]
    assert got.index('Newer') < got.index('Older')

    r = api_client.get(LIST_URL, {'ordering': 'created_at'})
    assert r.status_code == 200
    got = [b['title'] for b in r.json().get('results', [])]
    assert got.index('Older') < got.index('Newer')

@pytest.mark.django_db
def test_detail_returns_404_for_unapproved(api_client):
    '''
    Unapproved detail should not be publicly retrievable.
    '''
    ok = baker.make('bookmarks.Bookmark', title='OK', is_approved=True)
    no = baker.make('bookmarks.Bookmark', title="Nope", is_approved=False)

    r_ok = api_client.get(f'/bookmarks/v1/bookmarks/{ok.id}/')
    assert r_ok.status_code == 200

    r_no = api_client.get(f'/bookmarks/v1/bookmarks/{no.id}/')
    assert r_no.status_code == 404