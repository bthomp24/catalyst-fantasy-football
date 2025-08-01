from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import datetime, date
from ckeditor.fields import RichTextField

class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        #return reverse('article_detail', args=(str(self.id)))
        return reverse('home')

class Post(models.Model):
    title = models.CharField(max_length=255)
    title_tag = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    img_path = models.CharField(max_length=255, blank=True)
    podcast_path = models.CharField(max_length=255, blank=True)
    body = RichTextField(blank=True, null=True)
    post_date = models.DateField(auto_now_add=True)
    category = models.CharField(max_length=255, default='Uncategorized')


    def __str__(self):
        return self.title + ' | ' + str(self.author)
    
    def get_absolute_url(self):
        #return reverse('article_detail', args=(str(self.id)))
        return reverse('home')
    
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
        #return reverse('article_detail', args=(str(self.id)))
        return reverse('rankings')