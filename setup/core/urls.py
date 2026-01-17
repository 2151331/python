from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('buy/<int:stock_id>/', views.buy_stock, name='buy_stock'),
    path('blackjack/', views.blackjack_view, name='blackjack'),
]