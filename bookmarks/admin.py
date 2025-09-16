from django.contrib import admin
from django.utils import timezone, formats
from zoneinfo import ZoneInfo
from .models import Tag, Bookmark

# Register your models here.
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('title', 'domain', 'is_approved', 'created_local')
    list_filter = ('is_approved', 'domain', 'tags')
    search_fields = ('title', 'url', 'description')
    readonly_fields = ('submitted_ip', 'created_at', 'approved_at', 'approved_by', 'pending_tags')
    autocomplete_fields = ('tags',)
    date_hierarchy = 'created_at'
    list_per_page = 50

    # Attach bulk action
    actions = ['approve_selected']

    @admin.display(description='Created (CT)', ordering='-created_at')
    def created_local(self, obj):
        dt = timezone.localtime(obj.created_at, ZoneInfo('America/Chicago'))
        return formats.date_format(dt, 'DATETIME_FORMAT')

    @admin.action(description='Approve selected bookmarks')
    def approve_selected(self, request, queryset):
        # Approve bookmarks in bulk
        now = timezone.now()
        to_update = queryset.exclude(is_approved=True)
        updated = to_update.update(
            is_approved=True,
            approved_at=now,
            approved_by=request.user,
        )
        # Give feedback to admin UI
        self.message_user(request, f'Approved {updated} bookmark(s).')