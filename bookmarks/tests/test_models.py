import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from model_bakery import baker

@pytest.mark.django_db
def test_bookmark_save_sets_domain():
    '''
    Saving a bookmark computes `domain` from `url` (lowercased, stripes 'www.').
    '''
    b = baker.make(
        'bookmarks.Bookmark',
        url='https://www.Example.COM/path?q=1',
        domain='', # allow model.save() to compute
    )
    assert b.domain == 'example.com'

@pytest.mark.django_db
def test_bookmark_clean_disallows_non_http_schemes():
    '''
    Model.clean() should reject non-http(s) URLS like ftp://...
    '''
    from bookmarks.models import Bookmark
    bad = Bookmark(title='Bad', url='ftp://example.com', description='')
    with pytest.raises(ValidationError) as ei:
        bad.full_clean()
    assert 'url' in ei.value.error_dict

@pytest.mark.django_db
def test_bookmark_default_ordering_newest_first():
    '''
    Default ordering is -created_at (newest first).
    '''
    older = baker.make('bookmarks.Bookmark', created_at=timezone.now() - timedelta(days=1))
    newer = baker.make('bookmarks.Bookmark', created_at=timezone.now())

    titles = [b.title for b in type(older).objects.all()]
    assert titles.index(newer.title) < titles.index(older.title)

@pytest.mark.django_db
def test_tag_ordering_by_name():
    '''
    Tag default ordering is by name (A..Z).
    '''
    a = baker.make('bookmarks.Tag', slug='a', name='Aaa')
    z = baker.make('bookmarks.Tag', slug='z', name='Zzz')
    names = [t.name for t in type(a).objects.all()]
    assert names == ['Aaa', 'Zzz']