from django.db import models
from django.utils import timezone

# Create your models here.

class Player(models.Model):
    name = models.CharField(max_length=100)
    jersey_number = models.IntegerField()
    role = models.CharField(max_length=50, choices=[
        ('batsman', 'Batsman'),
        ('bowler', 'Bowler'),
        ('all_rounder', 'All-Rounder'),
        ('wicket_keeper', 'Wicket Keeper')
    ])
    batting_style = models.CharField(max_length=50, blank=True)
    bowling_style = models.CharField(max_length=50, blank=True)
    nationality = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    
    def __str__(self):
        return f"{self.name} ({self.role})"

class Team(models.Model):
    name = models.CharField(max_length=100)
    logo = models.URLField(blank=True)
    country = models.CharField(max_length=100)
    players = models.ManyToManyField(Player, through='TeamPlayer')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TeamPlayer(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    is_captain = models.BooleanField(default=False)
    is_keeper = models.BooleanField(default=False)
    joined_date = models.DateField()

class Match(models.Model):
    MATCH_STATUS = (
        ('upcoming', 'Upcoming'),
        ('live', 'Live'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('archived', 'Archived'),
    )

    title = models.CharField(max_length=200)
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team1_matches')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team2_matches')
    match_date = models.DateTimeField()
    venue = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=MATCH_STATUS, default='upcoming')
    
    # Toss details
    toss_winner = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='toss_won')
    toss_decision = models.CharField(max_length=20, choices=[('bat', 'Bat'), ('bowl', 'Bowl')], null=True, blank=True)
    
    # Score details
    team1_score = models.CharField(max_length=50, blank=True)
    team2_score = models.CharField(max_length=50, blank=True)
    winner = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches_won')
    
    # Match details
    overs = models.IntegerField(default=20)
    match_type = models.CharField(max_length=50, default='T20')
    description = models.TextField(blank=True)
    
    # Current match state
    current_innings = models.IntegerField(default=1)
    current_over = models.DecimalField(max_digits=4, decimal_places=1, default=0.0)
    batting_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='batting_matches')
    bowling_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='bowling_matches')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.team1} vs {self.team2} - {self.match_date.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-match_date']

class Over(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='overs')
    over_number = models.IntegerField()
    bowler = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='overs_bowled')
    runs = models.IntegerField(default=0)
    wickets = models.IntegerField(default=0)
    extras = models.IntegerField(default=0)
    innings = models.IntegerField()

    class Meta:
        ordering = ['innings', 'over_number']

class Ball(models.Model):
    BALL_TYPES = [
        ('regular', 'Regular'),
        ('wide', 'Wide'),
        ('no_ball', 'No Ball'),
        ('dead_ball', 'Dead Ball')
    ]

    SHOT_TYPES = [
        ('drive', 'Drive'),
        ('cut', 'Cut'),
        ('pull', 'Pull'),
        ('hook', 'Hook'),
        ('sweep', 'Sweep'),
        ('defense', 'Defense')
    ]

    over = models.ForeignKey(Over, on_delete=models.CASCADE, related_name='balls')
    ball_number = models.IntegerField()
    batsman = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='balls_faced')
    runs_scored = models.IntegerField(default=0)
    is_wicket = models.BooleanField(default=False)
    wicket_type = models.CharField(max_length=50, blank=True)
    ball_type = models.CharField(max_length=20, choices=BALL_TYPES, default='regular')
    shot_type = models.CharField(max_length=20, choices=SHOT_TYPES, null=True, blank=True)
    commentary = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['over', 'ball_number']

class PlayerInnings(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    innings = models.IntegerField()
    
    # Batting stats
    runs_scored = models.IntegerField(default=0)
    balls_faced = models.IntegerField(default=0)
    fours = models.IntegerField(default=0)
    sixes = models.IntegerField(default=0)
    how_out = models.CharField(max_length=100, blank=True)
    
    # Bowling stats
    overs_bowled = models.DecimalField(max_digits=4, decimal_places=1, default=0.0)
    runs_conceded = models.IntegerField(default=0)
    wickets = models.IntegerField(default=0)
    maidens = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['innings', '-runs_scored']
