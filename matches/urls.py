from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'matches', views.MatchViewSet)
router.register(r'teams', views.TeamViewSet)
router.register(r'players', views.PlayerViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('upcoming/', views.upcoming_matches, name='upcoming-matches'),
    path('live/', views.live_matches, name='live-matches'),
    path('recent/', views.recent_matches, name='recent-matches'),
]
