from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


   
class Player(models.Model):
    rank = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    team = models.CharField(max_length=255)
    position = models.CharField(max_length=255, choices=(('QB', 'QB'), ('RB', 'RB'), ('WR', 'WR'), ('TE', 'TE'), ('K', 'K'), ('DST', 'DST')))
    drafted = models.BooleanField(default=False)
    positional_rank = models.CharField(max_length=255, default="")
    adp = models.FloatField(default=0)
    bye = models.IntegerField(default=0)
    
    def __str__(self):
        return str(self.rank) + ' | ' + self.name + ' | ' + self.team + ' | ' + self.position
    
    def get_absolute_url(self):
        return reverse('rankings')


NUM_TEAMS = 14
NUM_ROUNDS = 15


class FantasyTeam(models.Model):
    name = models.CharField(max_length=100)
    slot = models.PositiveSmallIntegerField(unique=True)  # column position, 1-14

    class Meta:
        ordering = ['slot']

    def __str__(self):
        return self.name


class DraftPick(models.Model):
    round_number = models.PositiveSmallIntegerField()
    team = models.ForeignKey(FantasyTeam, on_delete=models.CASCADE, related_name='picks')
    overall_pick = models.PositiveSmallIntegerField(unique=True)
    player = models.OneToOneField(
        Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='draft_pick'
    )

    class Meta:
        ordering = ['overall_pick']
        unique_together = ('round_number', 'team')

    def __str__(self):
        player_name = self.player.name if self.player else 'Empty'
        return f"Pick {self.overall_pick} (Round {self.round_number}, {self.team.name}): {player_name}"