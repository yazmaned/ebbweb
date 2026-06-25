from django import forms
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import AuthenticationForm

class SetNewPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label='Parola belirleyin',
        widget=forms.PasswordInput,
    )
    new_password2 = forms.CharField(
        label='Parolayı tekrar edin',
        widget=forms.PasswordInput,
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Şifreler eşleşmiyor.')
        return cleaned_data


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label='Kullanıcı Adı')
    password = forms.CharField(label='Parola', widget=forms.PasswordInput)