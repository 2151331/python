from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('slots/', views.slots, name='slots'),
    path('blackjack/game/', views.blackjack_game, name='blackjack_game'),
    path('market/', views.market, name='market'),
    path('portfolio/', views.portfolio_view, name='portfolio'),
]