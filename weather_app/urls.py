from django.urls import path
from .views import CityWeather, index, city_autocomplete, SearchHistoryView

urlpatterns = [
    path('', index, name='index'),
    path('weather/city/<str:city_name>/', CityWeather.as_view(), name='city-weather'),
    path('city-autocomplete/', city_autocomplete, name='city-autocomplete'),
    path('search-history/', SearchHistoryView.as_view(), name='search-history'),
]
