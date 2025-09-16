from django.db import models
from django.conf import settings
from urllib.parse import urlsplit
from django.core.exceptions import ValidationError

# Create your models here.
class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Bookmark(models.Model):
    # Public Fields
    title = models.CharField(max_length=120)
    url = models.URLField()
    description = models.CharField(max_length=500)
    tags = models.ManyToManyField(Tag, related_name='bookmarks')
    pending_tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Private (admin) fields
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    submitted_ip = models.CharField(max_length=45, null=True, blank=True)
    domain = models.CharField(max_length=255, db_index=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_approved', '-created_at']),
        ]
        constraints = [
            models.UniqueConstraint(models.functions.Lower('url'), name='uniq_lower_url', violation_error_message='URL already submitted')
        ]

    def save(self, *args, **kwargs):
        '''
        Compute and set domain from url (overwrites any existing value).
        https://www.google.com -> google.com
        '''
        if self.url:
            host = urlsplit(self.url).netloc.lower()
            if host.startswith('www.'):
                host = host[4:]
            self.domain = host
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.url and not (self.url.startswith('http://') or self.url.startswith('https://')):
            raise ValidationError({'url': 'URL must start with http:// or https://'})

    def __str__(self):
        return self.title