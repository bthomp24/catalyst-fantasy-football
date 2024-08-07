from django.urls import path
from .views import *

urlpatterns = [
    #path('', views.home, name="home"),
    path('', HomeView, name="home"),
    path('articles', ArticleListView.as_view(), name="articles"),
    path('article/<int:pk>', ArticleDetailView.as_view(), name='article_detail'),
    path('add_post/', AddPostView.as_view(), name='add_post'),
    path('add_category/', AddCategoryView.as_view(), name='add_category'),
    path('article/edit/<int:pk>', UpdatePostView.as_view(), name='update_post'),
    path('article/<int:pk>/delete', DeletePostView.as_view(), name='delete_post'),
    path('category/<str:cats>/', CategoryView, name='category'),
    #path('category-list/', CategoryListView, name='category_list'),
    path('rankings/', RankingsView.as_view(), name="rankings"),
    path('clear_draft', clear_draft, name='clear_draft'),
]

