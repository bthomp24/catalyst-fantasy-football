from django import forms
from .models import *

class DraftForm(forms.ModelForm):

    def clean_name(self):
        name = self.cleaned_data['name']
        return name

    name = forms.CharField(max_length=255)

    class Meta:
        model = Player
        fields = ('name',)

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }
