from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages


# ------------------- DASHBOARD/HOME ---------------------------
def home(request):
    return render(request, 'home.html')


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
        else:
            messages.error(request, "Credenciais inválidas")
    return render(request, 'login.html')

# ------------------- REGISTRO ---------------------------

def register(request):
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Conta criada com sucesso")
        return redirect('core:login') 
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
            "title": "Sweet Bonanza",
            "img": "https://www.pragmaticplay.com/wp-content/uploads/2021/05/SweetBonanza-800x600.jpg",
            "url": "https://demogamesfree.pragmaticplay.net/gs2c/html5Game.do?extGame=1&symbol=vs20fruitswx&gname=Sweet%20Bonanza%201000&jurisdictionID=99&mgckey=stylename@generic~SESSION@ea979611-4a0b-4587-a0e5-0222c3ee266b"
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


# ------------------- MARCADO/INVESTIMENTOS ---------------------------

import random
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Profile

@login_required
def market(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    # Empresas fakes
    assets = [
        {"name": "TechCorp", "price": random.randint(80, 140)},
        {"name": "GreenEnergy", "price": random.randint(40, 90)},
        {"name": "CryptoX", "price": random.randint(10, 60)},
        {"name": "AI Industries", "price": random.randint(120, 200)},
    ]

    return render(request, "market.html", {
        "profile": profile,
        "assets": assets
    })


import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Asset, Portfolio, Transaction, Profile

@login_required
def market(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    assets = Asset.objects.all()

    # EVENTO ALEATÓRIO
    event = random.choice([None, None, "CRASH", "PUMP"])

    for asset in assets:
        variation = random.uniform(-5, 5)

        if event == "CRASH":
            variation -= random.uniform(5, 15)
        elif event == "PUMP":
            variation += random.uniform(5, 15)

        asset.price = max(1, round(asset.price + variation, 2))
        asset.save()

    if request.method == "POST":
        asset_id = request.POST["asset_id"]
        action = request.POST["action"]
        quantity = int(request.POST["quantity"])

        asset = Asset.objects.get(id=asset_id)
        total_price = asset.price * quantity

        portfolio, _ = Portfolio.objects.get_or_create(
            user=request.user, asset=asset
        )

        if action == "buy":
            if total_price > profile.balance:
                return redirect("core:market")

            profile.balance -= total_price
            profile.save()

            portfolio.avg_price = (
                (portfolio.avg_price * portfolio.quantity + total_price)
                / (portfolio.quantity + quantity)
            )
            portfolio.quantity += quantity
            portfolio.save()

            Transaction.objects.create(
                user=request.user, asset=asset,
                quantity=quantity, price=asset.price, type="BUY"
            )

        elif action == "sell":
            if quantity > portfolio.quantity:
                return redirect("core:market")

            portfolio.quantity -= quantity
            profile.balance += total_price

            if portfolio.quantity == 0:
                portfolio.avg_price = 0

            portfolio.save()
            profile.save()

            Transaction.objects.create(
                user=request.user, asset=asset,
                quantity=quantity, price=asset.price, type="SELL"
            )

    portfolio = Portfolio.objects.filter(user=request.user)
    history = Transaction.objects.filter(user=request.user).order_by("-created_at")[:10]

    return render(request, "market.html", {
        "assets": assets,
        "portfolio": portfolio,
        "history": history,
        "balance": profile.balance,
        "event": event
    })

