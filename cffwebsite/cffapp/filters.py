import django_filters
#from django import forms

from .models import *

class PositionFilter(django_filters.FilterSet):

    # position = django_filters.ModelChoiceFilter(
    #     queryset=Player.objects.all(),
    #     empty_label="All Positions",
    #     label="Position",
    #     widget=forms.Select(attrs={'class': 'form-control'}),
    #     )

    class Meta:
        model = Player
        fields = ['position',]