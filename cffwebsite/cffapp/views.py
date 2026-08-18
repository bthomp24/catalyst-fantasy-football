from django.shortcuts import render
from django_filters.views import FilterView
from .filters import PositionFilter
from .models import Player, FantasyTeam, DraftPick, NUM_TEAMS, NUM_ROUNDS
from .forms import *
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
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

                pick_info = None
                if pl.drafted:
                    # Auto-assign to the next open slot on the draft board (lowest
                    # overall pick number that doesn't have a player yet), if any remain.
                    next_pick = DraftPick.objects.filter(player__isnull=True).order_by('overall_pick').first()
                    if next_pick:
                        next_pick.player = pl
                        next_pick.save()
                        pick_info = {
                            'pick_id': next_pick.id,
                            'overall_pick': next_pick.overall_pick,
                            'round_number': next_pick.round_number,
                            'team_id': next_pick.team_id,
                        }
                else:
                    # Undo: if this player currently occupies a board slot, free it up.
                    existing_pick = DraftPick.objects.filter(player=pl).first()
                    if existing_pick:
                        pick_info = {
                            'pick_id': existing_pick.id,
                            'overall_pick': existing_pick.overall_pick,
                            'round_number': existing_pick.round_number,
                            'team_id': existing_pick.team_id,
                        }
                        existing_pick.player = None
                        existing_pick.save()

                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'name': pl.name,
                        'drafted': pl.drafted,
                        'pick': pick_info,
                    })
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
    Player.objects.filter(drafted=True).update(drafted=False)
    DraftPick.objects.exclude(player__isnull=True).update(player=None)

    redirect_to = request.META.get('HTTP_REFERER')
    if redirect_to:
        return HttpResponseRedirect(redirect_to)
    return HttpResponseRedirect('rankings')

def poll_draft_status(request):
    players = Player.objects.values('name', 'drafted')
    draft_status = {p['name']: p['drafted'] for p in players}
    return JsonResponse({'players': draft_status})


def ensure_draft_board_exists():
    """Idempotently sets up the 14 fantasy teams and 15x14 snake-ordered
    draft picks, the first time the draft board is visited."""
    if not FantasyTeam.objects.exists():
        for slot in range(1, NUM_TEAMS + 1):
            FantasyTeam.objects.create(name=f"Team {slot}", slot=slot)

    total_expected = NUM_TEAMS * NUM_ROUNDS
    if DraftPick.objects.count() < total_expected:
        teams = list(FantasyTeam.objects.order_by('slot'))
        existing = set(DraftPick.objects.values_list('round_number', 'team_id'))
        picks_to_create = []
        for round_number in range(1, NUM_ROUNDS + 1):
            # Snake order: odd rounds go team 1 -> 14, even rounds reverse.
            ordered_teams = teams if round_number % 2 == 1 else list(reversed(teams))
            for position_in_round, team in enumerate(ordered_teams, start=1):
                if (round_number, team.id) in existing:
                    continue
                overall = (round_number - 1) * NUM_TEAMS + position_in_round
                picks_to_create.append(
                    DraftPick(round_number=round_number, team=team, overall_pick=overall)
                )
        DraftPick.objects.bulk_create(picks_to_create)


@user_passes_test(lambda u: u.is_superuser)
def draft_board(request):
    ensure_draft_board_exists()

    teams = list(FantasyTeam.objects.order_by('slot'))
    picks = DraftPick.objects.select_related('team', 'player').order_by('overall_pick')

    board = {}
    for pick in picks:
        board.setdefault(pick.round_number, {})[pick.team_id] = pick

    rounds = []
    for round_number in range(1, NUM_ROUNDS + 1):
        cells = [board[round_number][team.id] for team in teams]
        rounds.append({'round_number': round_number, 'cells': cells})

    players = Player.objects.all().order_by('id')

    context = {
        'teams': teams,
        'rounds': rounds,
        'players': players,
    }
    return render(request, 'draft_board.html', context)


@user_passes_test(lambda u: u.is_superuser)
@require_POST
def assign_draft_pick(request):
    pick_id = request.POST.get('pick_id')
    player_id = request.POST.get('player_id')

    try:
        pick = DraftPick.objects.get(id=pick_id)
    except DraftPick.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pick not found'}, status=404)

    if pick.player_id is not None:
        return JsonResponse({'success': False, 'error': 'That pick is already filled'}, status=400)

    try:
        player = Player.objects.get(id=player_id)
    except Player.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Player not found'}, status=404)

    if player.drafted:
        return JsonResponse({'success': False, 'error': 'Player is already drafted'}, status=400)

    pick.player = player
    pick.save()
    player.drafted = True
    player.save()

    return JsonResponse({
        'success': True,
        'pick_id': pick.id,
        'player_id': player.id,
        'player_name': player.name,
        'position': player.position,
        'positional_rank': player.positional_rank,
        'team': player.team,
        'bye': player.bye,
    })


@user_passes_test(lambda u: u.is_superuser)
@require_POST
def clear_draft_pick(request):
    pick_id = request.POST.get('pick_id')

    try:
        pick = DraftPick.objects.select_related('player').get(id=pick_id)
    except DraftPick.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pick not found'}, status=404)

    player = pick.player
    pick.player = None
    pick.save()

    if player:
        player.drafted = False
        player.save()

    return JsonResponse({'success': True, 'pick_id': pick.id})


@user_passes_test(lambda u: u.is_superuser)
@require_POST
def update_team_name(request):
    team_id = request.POST.get('team_id')
    name = request.POST.get('name', '').strip()

    if not name:
        return JsonResponse({'success': False, 'error': 'Name cannot be blank'}, status=400)

    try:
        team = FantasyTeam.objects.get(id=team_id)
    except FantasyTeam.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Team not found'}, status=404)

    team.name = name[:100]
    team.save()

    return JsonResponse({'success': True, 'team_id': team.id, 'name': team.name})


@user_passes_test(lambda u: u.is_superuser)
def available_players(request):
    players = Player.objects.filter(drafted=False).order_by('id').values(
        'id', 'name', 'position', 'positional_rank', 'team'
    )
    return JsonResponse({'players': list(players)})


@user_passes_test(lambda u: u.is_superuser)
def poll_draft_board(request):
    picks = DraftPick.objects.values(
        'id', 'player_id', 'player__name', 'player__position',
        'player__positional_rank', 'player__team', 'player__bye',
    )
    pick_data = {
        p['id']: {
            'player_id': p['player_id'],
            'player_name': p['player__name'],
            'position': p['player__position'],
            'positional_rank': p['player__positional_rank'],
            'team': p['player__team'],
            'bye': p['player__bye'],
        }
        for p in picks
    }

    teams = FantasyTeam.objects.values('id', 'name')
    team_data = {t['id']: t['name'] for t in teams}

    return JsonResponse({'picks': pick_data, 'teams': team_data})