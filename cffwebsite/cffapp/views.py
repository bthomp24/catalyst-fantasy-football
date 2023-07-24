from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Post, Category, Player
from .forms import *
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect


#def home(request):
#    return render(request, 'home.html', {})

class HomeView(ListView):
    model = Post
    template_name = 'home.html'
    ordering = ['-id']

    # def get_context_data(self, *args, **kwargs):
    #     cat_menu = Category.objects.all()
    #     context = super(HomeView, self).get_context_data(*args, **kwargs)
    #     context["cat_menu"] = cat_menu
    #     return context


class ArticleDetailView(DetailView):
    model = Post
    template_name = 'article_details.html'

    # def get_context_data(self, *args, **kwargs):
    #     cat_menu = Category.objects.all()
    #     context = super(ArticleDetailView, self).get_context_data(*args, **kwargs)
    #     context["cat_menu"] = cat_menu
    #     return context

class AddPostView(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'add_post.html'
    #fields = '__all__'
    #fields = ('title', 'body')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class AddCategoryView(CreateView):
    model = Category
    #form_class = PostForm
    template_name = 'add_category.html'
    fields = '__all__'
    #fields = ('title', 'body')

def CategoryView(request, cats):
    category_posts = Post.objects.filter(category__iexact=cats.replace('-', ' ')).order_by('-id')
    return render(request, 'categories.html', {'cats':cats.title().replace('-', ' '), 'category_posts':category_posts})

# def CategoryListView(request):
#     cat_menu_list = Category.objects.all()
#     return render(request, 'category_list.html', {'cat_menu_list':cat_menu_list})

class UpdatePostView(UpdateView):
    model = Post
    form_class = EditForm
    template_name = 'update_post.html'
    #fields = ('title', 'title_tag', 'body

class DeletePostView(DeleteView):
    model = Post
    template_name = 'delete_post.html'
    success_url = reverse_lazy('home')

class RankingsView(ListView):
    model = Player
    template_name = 'rankings.html'
    context_object_name = 'players'

    def get_context_data(self, **kwargs):
        context = super(RankingsView, self).get_context_data(**kwargs)
        context['form'] = DraftForm()
        return context
    
    def post(self, request):
        form = DraftForm(request.POST)
        if form.is_valid():
            player_name = form.clean_name()
            pl = Player.objects.get(name__iexact=player_name)
            pl.drafted = True
            pl.save()
            #return redirect(reverse('rankings.html'))
            return HttpResponseRedirect(request.path_info)

def clear_draft(request):
    players = Player.objects.all()
    for player in players:
        if player.drafted:
            player.drafted = False
            player.save()

    #return redirect(RankingsView)
    return HttpResponseRedirect('rankings')