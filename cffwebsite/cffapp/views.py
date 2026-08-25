from django.shortcuts import render
from django_filters.views import FilterView
from .filters import PositionFilter
from .models import Player, FantasyTeam, DraftPick, NUM_TEAMS, NUM_ROUNDS
from .forms import *
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.db.models import F
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


def compute_my_pick_projection():
    """Figures out, for whichever FantasyTeam is marked is_my_team:
    - how many live (still-open) picks happen before my next turn, correctly
      skipping over any already-filled keeper slots wherever they fall
    - which currently-undrafted player would be "on the clock" for me,
      simulating that the other teams draft by ESPN rank (player.rank) and
      then taking the best remaining player by MY board rank (board_rank)

    Returns None if no team is marked as mine, or if my team has no
    remaining open picks (fully drafted / bench full)."""
    my_team = FantasyTeam.objects.filter(is_my_team=True).first()
    if not my_team:
        return None

    my_next_pick = (
        DraftPick.objects.filter(team=my_team, player__isnull=True)
        .order_by('overall_pick')
        .first()
    )
    if not my_next_pick:
        return None

    current_pointer = (
        DraftPick.objects.filter(player__isnull=True)
        .order_by('overall_pick')
        .first()
    )
    if not current_pointer:
        return None

    # Count only the still-open picks strictly between "now" and my next
    # pick - already-filled keeper slots in that range don't count, since
    # they don't represent a live selection happening in between. Because
    # my_next_pick is my team's EARLIEST open pick, every pick in this
    # range necessarily belongs to another team.
    picks_between = DraftPick.objects.filter(
        player__isnull=True,
        overall_pick__gte=current_pointer.overall_pick,
        overall_pick__lt=my_next_pick.overall_pick,
    ).count()

    def espn_rank_key(player):
        try:
            return float(player.rank)
        except (TypeError, ValueError):
            return float('inf')

    def board_rank_key(player):
        return player.board_rank if player.board_rank is not None else float('inf')

    undrafted = list(Player.objects.filter(drafted=False))

    # Simulate: the next `picks_between` live picks (all belonging to other
    # teams) go to the top ESPN-ranked undrafted players.
    by_espn_rank = sorted(undrafted, key=espn_rank_key)
    taken_by_others_ids = {p.id for p in by_espn_rank[:picks_between]}

    # From whatever's left after that, my projected pick is the best
    # remaining player according to MY board rankings.
    remaining = [p for p in undrafted if p.id not in taken_by_others_ids]
    remaining.sort(key=board_rank_key)
    projected_player = remaining[0] if remaining else None

    return {
        'my_team_id': my_team.id,
        'my_team_name': my_team.name,
        'next_pick_overall': my_next_pick.overall_pick,
        'next_pick_round': my_next_pick.round_number,
        'picks_between': picks_between,
        'projected_player_id': projected_player.id if projected_player else None,
        'projected_player_name': projected_player.name if projected_player else None,
    }


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

    players = Player.objects.all().order_by(F('board_rank').asc(nulls_last=True), 'id')
    projection = compute_my_pick_projection()

    context = {
        'teams': teams,
        'rounds': rounds,
        'players': players,
        'use_board_ranking': True,
        'projection': projection,
        'projected_pick_player_id': projection['projected_player_id'] if projection else None,
    }
    return render(request, 'draft_board.html', context)


@user_passes_test(lambda u: u.is_superuser)
@require_POST
def set_my_team(request):
    team_id = request.POST.get('team_id')

    try:
        team = FantasyTeam.objects.get(id=team_id)
    except FantasyTeam.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Team not found'}, status=404)

    FantasyTeam.objects.exclude(id=team.id).update(is_my_team=False)
    team.is_my_team = True
    team.save()

    projection = compute_my_pick_projection()
    return JsonResponse({'success': True, 'my_team_id': team.id, 'projection': projection})


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

    return JsonResponse({
        'picks': pick_data,
        'teams': team_data,
        'projection': compute_my_pick_projection(),
    })