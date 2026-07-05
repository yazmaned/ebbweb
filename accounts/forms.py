from django import forms
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(label='E-posta', required=True)
    phone_number = forms.CharField(
        label='Telefon Numarası',
        max_length=25,
        required=True,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Kullanıcı Adı'
        self.fields['password1'].label = 'Parola'
        self.fields['password2'].label = 'Parolayı Tekrar Girin'
        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''

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