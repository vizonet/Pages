""" Forms. """

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _


# Authentication form which uses Bootstrap CSS
class BootstrapAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(
            {
                'class': 'form-control',
                'placeholder': 'Имя пользователя',
            }
        )
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            {
                'class': 'form-control',
                'placeholder': 'Пароль',
            }
        )
    )
