import django_filters

from .models import *

class PositionFilter(django_filters.FilterSet):

    class Meta:
        model = Player
        fields = ['position',]