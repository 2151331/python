from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile, Stock, Transaction

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            # Removi o login(request, user) para forçar o utilizador a ir para a tela de login
            messages.success(request, "CONTA CRIADA COM SUCESSO! EFETUE O LOGIN.")
            return redirect('login') # Redireciona para a página de login
        else:
            messages.error(request, "ERRO NO REGISTO. VERIFIQUE OS REQUISITOS DA PALAVRA-PASSE.")
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard_view(request):
    # Garante que o perfil existe antes de carregar a página
    profile, created = Profile.objects.get_or_create(user=request.user)
    stocks = Stock.objects.all()
    ranking = Profile.objects.order_by('-balance')[:10]
    
    return render(request, 'dashboard.html', {
        'profile': profile,
        'stocks': stocks,
        'ranking': ranking
    })

@login_required
def buy_stock(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)
    profile = request.user.profile
    
    if profile.balance >= stock.current_price:
        profile.balance -= stock.current_price
        profile.save()
        
        Transaction.objects.create(
            user=request.user, 
            stock=stock, 
            purchase_price=stock.current_price
        )
        messages.success(request, f"ORDEM EXECUTADA: {stock.ticker} adquirido.")
    else:
        messages.error(request, "ERRO: Saldo insuficiente para completar a transação.")
        
    return redirect('dashboard')

from decimal import Decimal  
import random # Adicione esta importação no topo do ficheiro

import random
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def get_card_value(card):
    # card format: "10_S" (10 de Espadas) ou "A_H" (Ás de Copas)
    rank = card.split('_')[0]
    if rank in ['J', 'Q', 'K']: return 10
    if rank == 'A': return 11
    return int(rank)

def calculate_hand(hand):
    value = sum(get_card_value(card) for card in hand)
    aces = sum(1 for card in hand if card.startswith('A'))
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

@login_required
def blackjack_view(request):
    profile = request.user.profile
    session = request.session
    
    # Iniciar novo jogo / Definir Aposta
    if request.method == 'POST' and 'place_bet' in request.POST:
        try:
            bet = Decimal(request.POST.get('bet', 0))
            if bet < 10 or bet > profile.balance: raise ValueError
        except ValueError:
            messages.error(request, "Aposta inválida ou saldo insuficiente.")
            return redirect('blackjack')

        # Preparar baralho e dar cartas iniciais
        suits = ['S', 'H', 'D', 'C']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [f"{r}_{s}" for r in ranks for s in suits]
        random.shuffle(deck)
        
        session['deck'] = deck
        session['player_hand'] = [deck.pop(), deck.pop()]
        session['dealer_hand'] = [deck.pop(), deck.pop()]
        session['bet'] = str(bet)
        session['game_active'] = True
        return redirect('blackjack')

    # HIT (Pedir Carta)
    if request.method == 'POST' and 'hit' in request.POST:
        deck = session.get('deck')
        player_hand = session.get('player_hand')
        player_hand.append(deck.pop())
        session['player_hand'] = player_hand
        session['deck'] = deck
        
        if calculate_hand(player_hand) > 21:
            # BUST (Estourou)
            profile.balance -= Decimal(session['bet'])
            profile.save()
            messages.error(request, f"ESTOUROU! Perdeu {session['bet']}€")
            session['game_active'] = False
        return redirect('blackjack')

    # STAND (Parar)
    if request.method == 'POST' and 'stand' in request.POST:
        deck = session.get('deck')
        dealer_hand = session.get('dealer_hand')
        player_hand = session.get('player_hand')
        
        # Dealer joga (para nos 17)
        while calculate_hand(dealer_hand) < 17:
            dealer_hand.append(deck.pop())
        
        p_score = calculate_hand(player_hand)
        d_score = calculate_hand(dealer_hand)
        bet = Decimal(session['bet'])
        
        if d_score > 21 or p_score > d_score:
            profile.balance += bet
            messages.success(request, f"GANHOU! +{bet}€")
        elif p_score < d_score:
            profile.balance -= bet
            messages.error(request, f"DERROTA! -{bet}€")
        else:
            messages.info(request, "EMPATE!")
            
        profile.save()
        session['dealer_hand'] = dealer_hand
        session['game_active'] = False
        return redirect('blackjack')

    context = {
        'profile': profile,
        'game_active': session.get('game_active', False),
        'player_hand': session.get('player_hand'),
        'dealer_hand': session.get('dealer_hand'),
        'p_score': calculate_hand(session.get('player_hand', [])),
        'd_score': calculate_hand(session.get('dealer_hand', [])),
        'bet': session.get('bet')
    }
    return render(request, 'blackjack.html', context)