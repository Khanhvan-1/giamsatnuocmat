import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
@csrf_exempt
def proxy_nominatim_search(request):
    q = request.GET.get('q', '')
    limit = request.GET.get('limit', 8)
    countrycodes = request.GET.get('countrycodes', 'vn')
    viewbox = request.GET.get('viewbox', '')
    bounded = request.GET.get('bounded', '')
    lat = request.GET.get('lat', '')
    lon = request.GET.get('lon', '')
    radius = request.GET.get('radius', '')
    
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'format': 'json',
        'q': q,
        'limit': limit,
        'countrycodes': countrycodes,
        'addressdetails': 1,
    }
    if viewbox:
        params['viewbox'] = viewbox
        params['bounded'] = 1
    if lat and lon:
        params['lat'] = lat
        params['lon'] = lon
        params['radius'] = radius if radius else 5000
    
    headers = {
        'User-Agent': 'WaterQualityGIS/1.0 (your_email@example.com)'  # Thay email thật
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        return JsonResponse(resp.json(), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
@csrf_exempt
def proxy_nominatim_reverse(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    if not lat or not lon:
        return JsonResponse({'error': 'Missing lat/lon'}, status=400)
    url = 'https://nominatim.openstreetmap.org/reverse'
    params = {
        'format': 'json',
        'lat': lat,
        'lon': lon,
        'zoom': 18,
        'addressdetails': 1,
    }
    headers = {'User-Agent': 'WaterQualityGIS/1.0 (your_email@example.com)'}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        return JsonResponse(resp.json())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)