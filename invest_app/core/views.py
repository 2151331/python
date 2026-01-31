from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages


# ------------------- DASHBOARD/HOME ---------------------------

def home(request):
    profile = request.user.profile
    return render(request, 'home.html', {
        'profile': profile
    })


# ------------------- LOGIN ---------------------------
def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)
            messages.success(request, "Login efetuado com sucesso")
            return redirect('core:home')
            #tem que ser core:home pq está defenido nas urls como app_name=core 
        else:
            messages.error(request, "Credenciais inválidas")
    return render(request, 'login.html')

# ------------------- REGISTO ---------------------------

def register(request):
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Conta criada com sucesso")
        return redirect('core:login')
        #ao fazer o registo, redireciona para a página de login e guarda na base de dados.
    return render(request, 'register.html', {'form': form})

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Profile
from .forms import BetForm
import random

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Profile
from .forms import BetForm
import requests


# ------------------- SLOTS ---------------------------

@login_required
def slots(request):
    slots_list = [
        {
            "title": "Sweet Bonanza 1000",
            "img": "https://www.pragmaticplay.com/wp-content/uploads/2024/05/Sweet-Bonanza-1000_339x180.png",
            "url": "https://demogamesfree.pragmaticplay.net/gs2c/openGame.do?gameSymbol=vs20fruitswx&websiteUrl=https%3A%2F%2Fdemogamesfree.pragmaticplay.net&jurisdiction=99&lobby_url=https%3A%2F%2Fwww.pragmaticplay.com%2Fen%2F&lang=en&cur=USD&lang=EN&cur=USD"
        },
        {
            "title": "Wheel of Happiness",
            "img": "https://www.pragmaticplay.com/wp-content/uploads/2025/12/Wheel-of-Happiness_339x180_EN.png",
            "url": "https://demogamesfree.pragmaticplay.net/gs2c/openGame.do?gameSymbol=vswayswildeq&websiteUrl=https%3A%2F%2Fdemogamesfree.pragmaticplay.net&jurisdiction=99&lobby_url=https%3A%2F%2Fwww.pragmaticplay.com%2Fen%2F&lang=en&cur=USD&lang=EN&cur=USD"
        },
        {
            "title": "Fortune Of Olympus",
            "img": "https://www.pragmaticplay.com/wp-content/uploads/2025/11/Fortune-of-Olympus_339x180_EN.png",
            "url": "https://demogamesfree.pragmaticplay.net/gs2c/openGame.do?gameSymbol=vs20olympgcl&websiteUrl=https%3A%2F%2Fdemogamesfree.pragmaticplay.net&jurisdiction=99&lobby_url=https%3A%2F%2Fwww.pragmaticplay.com%2Fen%2F&lang=en&cur=USD&lang=EN&cur=USD"
        }
    ]

    return render(request, "slots.html", {
        "slots_list": slots_list
    })


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Profile
from .forms import BetForm
import requests


# ------------------- BLACKJACK ---------------------------

@login_required
def blackjack_game(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    message = ""
    player_cards = []
    dealer_cards = []

    # Criar deck novo ou pegar deck da sessão
    deck_id = request.session.get('deck_id')
    if not deck_id:
        res = requests.get('https://deckofcardsapi.com/api/deck/new/shuffle/?deck_count=1')
        deck_id = res.json()['deck_id']
        request.session['deck_id'] = deck_id

    if request.method == "POST":
        form = BetForm(request.POST)
        if form.is_valid():
            bet = form.cleaned_data['bet_amount']

            if bet > profile.balance:
                message = "Saldo insuficiente!"
            else:
                # Deduz aposta do saldo
                profile.balance -= bet
                profile.save()

                # Comprar cartas da API
                player_res = requests.get(f'https://deckofcardsapi.com/api/deck/{deck_id}/draw/?count=2')
                dealer_res = requests.get(f'https://deckofcardsapi.com/api/deck/{deck_id}/draw/?count=2')

                player_cards = player_res.json()['cards']
                dealer_cards = dealer_res.json()['cards']

                # Função simples para valores
                def card_value(card):
                    if card['value'] in ['JACK','QUEEN','KING']:
                        return 10
                    if card['value'] == 'ACE':
                        return 11
                    return int(card['value'])

                def hand_value(cards):
                    value = sum(card_value(c) for c in cards)
                    aces = sum(1 for c in cards if c['value']=='ACE')
                    while value>21 and aces>0:
                        value -= 10
                        aces -=1
                    return value

                player_total = hand_value(player_cards)
                dealer_total = hand_value(dealer_cards)

                # Dealer compra até 17
                while dealer_total < 17:
                    draw = requests.get(f'https://deckofcardsapi.com/api/deck/{deck_id}/draw/?count=1').json()['cards']
                    dealer_cards += draw
                    dealer_total = hand_value(dealer_cards)

                # Determinar resultado
                if player_total>21:
                    result = "Perdeu!"
                elif dealer_total>21 or player_total>dealer_total:
                    result = "Ganhou!"
                    profile.balance += bet*2
                    profile.save()
                elif player_total==dealer_total:
                    result = "Empate!"
                    profile.balance += bet
                    profile.save()
                else:
                    result = "Perdeu!"

                message = f"{result} | Você: {player_total} | Dealer: {dealer_total}"

    else:
        form = BetForm()

    return render(request, 'blackjack_game.html', {
        'form': form,
        'profile': profile,
        'message': message,
        'player_cards': player_cards,
        'dealer_cards': dealer_cards,
    })


# ------------------- AÇÕES/INVESTIMENTOS ---------------------------

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
import json

@login_required
def market(request):
    """Lista ativos e processa a compra com proteção de transação."""
    from .models import Asset, Profile, Portfolio, Transaction

    assets = Asset.objects.all()
    # Garante que o profile existe
    user_profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        asset_id = request.POST.get('asset_id')
        qty_str = request.POST.get('quantity', '0')

        if not qty_str.isdigit() or int(qty_str) <= 0:
            messages.error(request, "QUANTIDADE INVÁLIDA")
            return redirect('core:market_cenas')

        quantity = int(qty_str)
        asset = get_object_or_404(Asset, id=asset_id)
        
        # Conversão para Decimal para evitar erro: Decimal - Float
        total_cost = Decimal(str(asset.price)) * quantity

        with transaction.atomic():
            # select_for_update bloqueia a linha no banco para evitar gastos duplos
            profile = Profile.objects.select_for_update().get(user=request.user)

            if profile.balance >= total_cost:
                # 1. Deduzir Saldo
                profile.balance -= total_cost
                profile.save()

                # 2. Registrar Histórico
                Transaction.objects.create(
                    user=request.user, asset=asset, quantity=quantity,
                    price=asset.price, type='BUY'
                )

                # 3. Atualizar Portfolio
                port, created = Portfolio.objects.get_or_create(user=request.user, asset=asset)
                
                # Cálculo de Preço Médio (PM)
                total_invested = (port.quantity * port.avg_price) + (quantity * asset.price)
                new_total_qty = port.quantity + quantity
                
                port.avg_price = total_invested / new_total_qty
                port.quantity = new_total_qty
                port.save()

                messages.success(request, f"SUCESSO: {quantity}x {asset.name} COMPRADAS")
            else:
                messages.error(request, "SALDO INSUFICIENTE NO TERMINAL")
        
        return redirect('core:market_cenas')

    # Dados para o gráfico do Chart.js
    chart_labels = [a.name for a in assets]
    chart_data = [a.price for a in assets]

    return render(request, 'market.html', {
        'assets': assets,
        'balance': user_profile.balance,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    })

@login_required
def portfolio_view(request):
    """Exibe a composição da carteira e gráfico de pizza."""
    from .models import Portfolio, Profile

    user_assets = Portfolio.objects.filter(user=request.user, quantity__gt=0)
    user_profile = request.user.profile

    labels = []
    values = []
    total_equity = 0

    for item in user_assets:
        # Valor atual baseado no preço de mercado do ativo
        current_val = item.quantity * item.asset.price
        labels.append(item.asset.name)
        values.append(current_val)
        total_equity += current_val

    return render(request, 'portfolio.html', {
        'portfolio': user_assets,
        'balance': user_profile.balance,
        'total_equity': total_equity,
        'chart_labels': json.dumps(labels),
        'chart_data': json.dumps(values),
    })