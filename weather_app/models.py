from django.db import models

class Weather(models.Model):
    city = models.CharField(max_length=100)
    date = models.DateField()
    temperature = models.FloatField()
    description = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.city} - {self.date}'

class SearchHistory(models.Model):
    city = models.CharField(max_length=100)
    search_count = models.IntegerField(default=0)

    def __str__(self):
        return self.city
