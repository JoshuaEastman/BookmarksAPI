from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'bookmarks'

urlpatterns = [
    path('docs/', TemplateView.as_view(template_name='bookmarks/swagger_docs.html'), name='bookmarks-docs'),
    path('v1/health/', views.HealthCheckView.as_view(), name='bookmarks-health'),
    path('v1/bookmarks/', views.BookmarkListView.as_view(), name='bookmarks-list'),
    path('v1/bookmarks/<int:id>/', views.BookmarkDetailView.as_view(), name='bookmarks-detail'),
    path('v1/bookmarks/submit/', views.BookmarkSubmitView.as_view(), name='bookmarks-submit'),
    path('demo/', TemplateView.as_view(template_name='bookmarks/bookmarks_demo.html'), name='bookmarks-demo'),
]
