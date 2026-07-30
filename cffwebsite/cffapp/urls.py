from django.urls import path
from .views import *

urlpatterns = [
    path('', RankingsView.as_view(), name="rankings"),
    path('rankings/', RankingsView.as_view(), name="rankings"),
    path('rankings/poll/', poll_draft_status, name='poll_draft_status'),
    path('clear_draft', clear_draft, name='clear_draft'),
]