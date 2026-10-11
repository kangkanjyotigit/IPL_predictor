from celery import shared_task
from django.utils import timezone
from .models import Match

@shared_task
def update_match_statuses():
    # Update match statuses based on match_date
    now = timezone.now()
    
    # Set matches to live that should have started
    Match.objects.filter(
        status='upcoming',
        match_date__lte=now
    ).update(status='live')
    
    # Set matches to completed that should have ended (assuming 4 hours duration)
    Match.objects.filter(
        status='live',
        match_date__lte=now - timezone.timedelta(hours=4)
    ).update(status='completed')

@shared_task
def cleanup_old_matches():
    # Archive matches older than 30 days
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    Match.objects.filter(
        match_date__lt=thirty_days_ago,
        status='completed'
    ).update(status='archived')
