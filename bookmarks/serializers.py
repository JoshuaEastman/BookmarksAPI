from urllib.parse import urlsplit, urlunsplit
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.exceptions import ParseError
from .models import Tag, Bookmark

# Helper to catch duplicate urls
def _canon_url(raw: str) -> str:
    raw = raw.strip()
    parts = urlsplit(raw)
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()

    if scheme == 'http' and netloc.endswith(':80'):
        netloc = netloc[:-3]
    if scheme == 'https' and netloc.endswith(':443'):
        netloc = netloc[:-4]

    path = parts.path or '/'

    return urlunsplit((scheme, netloc, path, parts.query, ''))

class BookmarkReadSerializer(serializers.ModelSerializer):
    tags = serializers.SlugRelatedField(many=True, slug_field='slug', read_only=True)

    class Meta:
        model = Bookmark
        fields = ['id', 'title', 'url', 'description', 'tags', 'created_at']

class BookmarkWriteSerializer(serializers.ModelSerializer):
    website = serializers.CharField(write_only=True, required=False, allow_blank=True)
    tags = serializers.ListField(
        child=serializers.CharField(min_length=1, max_length=50),
        required=True,
        allow_empty=False
    )

    class Meta:
        model = Bookmark
        fields = ['title', 'url', 'description', 'tags', 'website']

    def validate(self, attrs):
        # Honeypot: any content trips it -> reject
        if attrs.get('website'):
            raise ParseError('Invalid submission')
        attrs.pop('website', None) # drop before create()
        return attrs

    def validate_url(self, value):
        # Ensure url scheme is http or https
        if not value.startswith(('http://', 'https://')):
            raise ParseError('URL must start with http:// or https://')

        canon = _canon_url(value)

        # Pre-check to give 400 if duplicate url
        if Bookmark.objects.filter(url__iexact=canon).exists():
            raise ParseError('URL already submitted')

        return canon

    def create(self, validated_data):
        # Create a moderated (is_approved=False) bookmark and attach tags.
        # Get submitted tags
        submitted = list({s.strip().lower() for s in validated_data.pop('tags', []) if s and s.strip()})

        # Get known Tag objects and slugs
        known_tags = list(Tag.objects.filter(slug__in=submitted))
        known_slugs = {t.slug for t in known_tags}

        # Compute unknown slugs
        unknown = [s for s in submitted if s not in known_slugs]

        # Force moderation
        validated_data['pending_tags'] = unknown
        validated_data['is_approved'] = False

        # Trim user inputs
        validated_data['title'] = validated_data['title'].strip()
        validated_data['description'] = validated_data['description'].strip()

        # Create the bookmark
        try:
            bookmark = Bookmark.objects.create(**validated_data)
        except IntegrityError:
            raise ParseError('URL already submitted')

        # Attach M2M tags after the instance exists
        if known_tags:
            bookmark.tags.set(known_tags)

        return bookmark

class BookmarkSubmissionSerializer(serializers.ModelSerializer):
    tags = serializers.SlugRelatedField(many=True, slug_field='slug', read_only=True)
    pending_tags = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = Bookmark
        fields = ['id', 'title', 'url', 'description', 'tags', 'pending_tags', 'is_approved', 'created_at']