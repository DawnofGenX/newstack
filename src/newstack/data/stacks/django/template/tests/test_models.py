from datetime import timedelta

import pytest
from django.utils import timezone

from core.models import Item

pytestmark = pytest.mark.django_db


def test_str_returns_name():
    assert str(Item(name="Widget")) == "Widget"


def test_default_ordering_is_newest_first():
    older = Item.objects.create(name="older")
    Item.objects.create(name="newer")
    Item.objects.filter(pk=older.pk).update(created=timezone.now() - timedelta(days=1))

    assert [item.name for item in Item.objects.all()] == ["newer", "older"]
