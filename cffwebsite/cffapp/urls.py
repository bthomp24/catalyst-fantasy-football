from django.urls import path
from .views import *

urlpatterns = [
    path('', RankingsView.as_view(), name="rankings"),
    path('rankings/', RankingsView.as_view(), name="rankings"),
    path('rankings/poll/', poll_draft_status, name='poll_draft_status'),
    path('clear_draft', clear_draft, name='clear_draft'),
    path('draft-board/', draft_board, name='draft_board'),
    path('draft-board/assign/', assign_draft_pick, name='assign_draft_pick'),
    path('draft-board/clear/', clear_draft_pick, name='clear_draft_pick'),
    path('draft-board/update-team/', update_team_name, name='update_team_name'),
    path('draft-board/available-players/', available_players, name='available_players'),
    path('draft-board/poll/', poll_draft_board, name='poll_draft_board'),
]