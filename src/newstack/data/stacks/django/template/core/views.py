from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Item


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@require_GET
def items(request):
    payload = [
        {
            "id": item.pk,
            "name": item.name,
            "created": item.created.isoformat(),
        }
        for item in Item.objects.all()
    ]
    return JsonResponse(payload, safe=False)
