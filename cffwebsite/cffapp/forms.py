from django import forms
from .models import *

#choices = [('podcast', 'podcast'), ('rankings', 'rankings'), ('advice', 'advice'),]
cats = Category.objects.all().values_list('name', 'name')

cat_list = []
for item in cats:
    cat_list.append(item)

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'title_tag', 'category', 'img_path', 'podcast_path', 'body')

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'title_tag': forms.TextInput(attrs={'class': 'form-control'}),
            #'author': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(choices=cat_list, attrs={'class': 'form-control'}),
            'img_path': forms.TextInput(attrs={'class': 'form-control'}),
            'podcast_path': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control'}),
        }


class EditForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'title_tag', 'img_path', 'podcast_path', 'body')

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'title_tag': forms.TextInput(attrs={'class': 'form-control'}),
            'img_path': forms.TextInput(attrs={'class': 'form-control'}),
            'podcast_path': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control'}),
        }

class DraftForm(forms.ModelForm):
    #name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

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
