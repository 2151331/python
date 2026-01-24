from django import forms

class BetForm(forms.Form):
    bet_amount = forms.DecimalField(min_value=1, decimal_places=2, max_digits=12)
