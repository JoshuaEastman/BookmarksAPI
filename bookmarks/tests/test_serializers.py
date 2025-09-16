import pytest
from model_bakery import baker

@pytest.mark.django_db
def test_write_serializer_trims_inputs_and_splits_tags():
    '''
    BookmarkWriteSerializer:
    - trims title/url/description
    - known tags -> M2M tags
    - unknown tags -> pending_tags
    - forces is_approved=False
    - ignored honeypot 'website'
    '''
    # Ensure known tag is present in DB
    baker.make('bookmarks.Tag', slug='django', name='Django')

    from bookmarks.serializers import BookmarkWriteSerializer

    payload = {
        'title': ' Great Django Guide ',
        'url': ' https://djangoproject.com ',
        'description': ' A nice site ',
        'tags': ['django', 'api', 'tools'], # only django exists (created above)
        'website': 'bot-fill-should-be-ignored',
    }

    ser = BookmarkWriteSerializer(data=payload)
    assert ser.is_valid(), ser.errors

    obj = ser.save()
    obj.refresh_from_db()

    assert obj.title == 'Great Django Guide'
    assert obj.url == 'https://djangoproject.com'
    assert obj.description == 'A nice site'

    saved = list(obj.tags.values_list('slug', flat=True))
    assert saved == ['django']
    assert set(obj.pending_tags) == {'api', 'tools'}
    assert obj.is_approved is False

@pytest.mark.django_db
def test_write_serializer_rejects_bad_url():
    '''
    Serializer enforces ^https?:// URL pattern.
    '''
    from bookmarks.serializers import BookmarkWriteSerializer

    payload = {
        'title': 'Bad URL',
        'url': 'ftp://not-allowed',
        'description': '',
        'tags': ['misc'],
        'website': '',
    }
    ser = BookmarkWriteSerializer(data=payload)
    assert not ser.is_valid()
    assert 'url' in ser.errors