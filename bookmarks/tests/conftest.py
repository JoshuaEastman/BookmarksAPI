import pytest
from django.core.cache import cache
from django.utils import timezone

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()