from functools import wraps
from django.http import JsonResponse
from .models import APIKey

def require_api_key(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Api-Key '):
            return JsonResponse({'error': 'Missing or invalid Authorization header'}, status=401)

        key = auth_header.split(' ')[1].strip()
        try:
            api_key_obj = APIKey.objects.get(key=key)
            request.user = api_key_obj.user
        except APIKey.DoesNotExist:
            return JsonResponse({'error': 'Invalid API Key'}, status=403)

        return view_func(request, *args, **kwargs)

    return wrapper
