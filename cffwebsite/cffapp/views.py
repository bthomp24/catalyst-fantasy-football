from django.shortcuts import render
from django_filters.views import FilterView
from .filters import PositionFilter
from .models import Player
from .forms import *
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse
from django import template

register = template.Library()

def HomeView(request):
    return render(request, 'home.html')

class RankingsView(FilterView):
    model = Player
    template_name = 'rankings.html'
    paginate_by = 50
    filterset_class = PositionFilter
    context_object_name = 'players'

    def get_context_data(self, **kwargs):
        context = super(RankingsView, self).get_context_data(**kwargs)
        context['form'] = DraftForm()
        return context
    
    def post(self, request):
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        form = DraftForm(request.POST)

        if form.is_valid():
            player_name = form.clean_name()
            if Player.objects.filter(name__iexact=player_name).exists():
                pl = Player.objects.get(name__iexact=player_name)
                pl.drafted = not pl.drafted
                pl.save()
                if is_ajax:
                    return JsonResponse({'success': True, 'name': pl.name, 'drafted': pl.drafted})
            else:
                print("Player not found")
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Player not found'}, status=404)
            #return redirect(reverse('rankings.html'))
            return HttpResponseRedirect(request.path_info)

        if is_ajax:
            return JsonResponse({'success': False, 'error': 'Invalid form submission'}, status=400)
        return HttpResponseRedirect(request.path_info)
        

def clear_draft(request):
    players = Player.objects.all()
    for player in players:
        if player.drafted:
            player.drafted = False
            player.save()

    return HttpResponseRedirect('rankings')

def poll_draft_status(request):
    players = Player.objects.values('name', 'drafted')
    draft_status = {p['name']: p['drafted'] for p in players}
    return JsonResponse({'players': draft_status})