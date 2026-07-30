from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


   
class Player(models.Model):
    rank = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    team = models.CharField(max_length=255)
    position = models.CharField(max_length=255, choices=(('QB', 'QB'), ('RB', 'RB'), ('WR', 'WR'), ('TE', 'TE'), ('K', 'K'), ('DST', 'DST')))
    drafted = models.BooleanField(default=False)
    positional_rank = models.CharField(max_length=255, default="")
    adp = models.FloatField(default=0)
    bye = models.IntegerField(default=0)
    
    def __str__(self):
        return str(self.rank) + ' | ' + self.name + ' | ' + self.team + ' | ' + self.position
    
    def get_absolute_url(self):
        return reverse('rankings')