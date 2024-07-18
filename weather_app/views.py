from django.shortcuts import render
from django.conf import settings
import requests
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from .models import SearchHistory
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from urllib.parse import unquote


# Представление для получения прогноза погоды по городу через API
class CityWeather(APIView):
    def get(self, request, city_name):
        city_name = unquote(city_name)  # Декодируем URL параметр
        geolocator = Nominatim(user_agent="weather_app")
        location = geolocator.geocode(city_name)

        if not location:
            return Response({'error': 'City not found'}, status=status.HTTP_404_NOT_FOUND)

        latitude = location.latitude
        longitude = location.longitude
        url = f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m'

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            return Response({'error': 'Request to the weather service timed out'}, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        data = response.json()
        if 'hourly' not in data or 'temperature_2m' not in data['hourly']:
            return Response({'error': 'Weather data not available'}, status=status.HTTP_404_NOT_FOUND)

        weather_data = {
            'city': city_name,
            'latitude': latitude,
            'longitude': longitude,
            'temperature': data['hourly']['temperature_2m'][0]  # Температура в первый час
        }

        response = Response(weather_data, status=status.HTTP_200_OK, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        print(response)
        return response

# Представление для отображения главной страницы и получения прогноза погоды
def index(request):
    weather_data = None
    error = None
    city_name = request.GET.get('city_name')

    if city_name:
        city_name = unquote(city_name)  # Декодируем URL параметр

    if not city_name:
        city_name = request.COOKIES.get('last_city')

    if city_name:
        geolocator = Nominatim(user_agent="weather_app")
        location = geolocator.geocode(city_name)

        if not location:
            error = 'City not found'
        else:
            # Сохранение или обновление истории запросов
            search_history, created = SearchHistory.objects.get_or_create(city=city_name)
            search_history.search_count += 1
            search_history.save()

            latitude = location.latitude
            longitude = location.longitude
            url = f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=temperature_2m_max&timezone=auto'

            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()

                if 'daily' not in data or 'temperature_2m_max' not in data['daily']:
                    error = 'Weather data not available'
                else:
                    weather_data = {
                        'city': city_name,
                        'daily': [
                            {'date': (datetime.utcnow() + timedelta(days=i)).strftime('%Y-%m-%d'), 'temperature': temp}
                            for i, temp in enumerate(data['daily']['temperature_2m_max'])
                        ]
                    }
            except requests.exceptions.Timeout:
                error = 'Request to the weather service timed out'
            except requests.exceptions.RequestException as e:
                error = str(e)

    response = render(request, 'weather/index.html', {'weather_data': weather_data, 'error': error})
    if city_name:
        response.set_cookie('last_city', city_name, samesite='Lax')

    # Переопределение заголовка для использования UTF-8 кодировки
    response['Content-Type'] = 'text/html; charset=utf-8'
    print(response)
    return response

# Представление для автодополнения городов
def city_autocomplete(request):
    if 'term' in request.GET:
        term = request.GET.get('term')
        term = unquote(term)  # Декодируем URL параметр
        geolocator = Nominatim(user_agent="weather_app")
        try:
            locations = geolocator.geocode(term, exactly_one=False, limit=10)
            results = [location.address for location in locations] if locations else []
        except GeocoderTimedOut:
            results = []
        response = JsonResponse(results, safe=False, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response
    response = JsonResponse([], safe=False, json_dumps_params={'ensure_ascii': False})
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response

# Представление для отображения истории запросов
class SearchHistoryView(APIView):
    def get(self, request):
        search_history = SearchHistory.objects.all()
        data = {entry.city: entry.search_count for entry in search_history}
        response = Response(data)
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response

