from django.test import TestCase

from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from django.http import JsonResponse
import json


class WeatherAppTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.index_url = reverse('index')
        self.city_autocomplete_url = reverse('city-autocomplete')
        self.city_weather_url = lambda city_name: reverse('city-weather', args=[city_name])

    @patch('weather_app.views.Nominatim.geocode')
    def test_city_autocomplete(self, mock_geocode):#Проверяет, что автодополнение городов работает корректно.
        mock_geocode.return_value = [type('Location', (object,), {'address': 'Kazan, Russia'})]

        response = self.client.get(self.city_autocomplete_url, {'term': 'Kazan'})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIn('Kazan, Russia', data)

    @patch('weather_app.views.Nominatim.geocode')
    @patch('weather_app.views.requests.get')
    def test_index_view_with_valid_city(self, mock_requests_get, mock_geocode):#Проверяет, что главная страница корректно отображает прогноз погоды для валидного города.
        mock_geocode.return_value = type('Location', (object,), {'latitude': 55.7558, 'longitude': 37.6173})

        mock_response_data = {
            'daily': {
                'temperature_2m_max': [10, 15, 20]
            }
        }
        mock_response = type('Response', (object,), {'json': lambda: mock_response_data})
        mock_requests_get.return_value = mock_response

        response = self.client.get(self.index_url, {'city_name': 'Kazan, Russia'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kazan, Russia')
        self.assertContains(response, '10°C')
        self.assertContains(response, '15°C')
        self.assertContains(response, '20°C')

    @patch('weather_app.views.Nominatim.geocode')
    def test_index_view_with_invalid_city(self, mock_geocode):#Проверяет, что главная страница корректно обрабатывает невалидный город.
        mock_geocode.return_value = None

        response = self.client.get(self.index_url, {'city_name': 'InvalidCity'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'City not found')

    @patch('weather_app.views.Nominatim.geocode')
    @patch('weather_app.views.requests.get')
    def test_city_weather_view(self, mock_requests_get, mock_geocode):#Проверяет, что API для получения прогноза погоды по городу работает корректно
        mock_geocode.return_value = type('Location', (object,), {'latitude': 55.7558, 'longitude': 37.6173})

        mock_response_data = {
            'hourly': {
                'temperature_2m': [5]
            }
        }
        mock_response = type('Response', (object,), {'json': lambda: mock_response_data})
        mock_requests_get.return_value = mock_response

        response = self.client.get(self.city_weather_url('Kazan, Russia'))
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['city'], 'Kazan, Russia')
        self.assertEqual(data['temperature'], 5)
