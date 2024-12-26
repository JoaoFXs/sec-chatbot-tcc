from django import forms
from django.contrib.auth import authenticate

class AlunoAuthenticationForm(forms.Form):
    ra = forms.CharField(label='ra',  widget=forms.TextInput(attrs={
            'placeholder': 'INSIRA SEU R.A',
            'class': 'form-control'  # Adicione outras classes CSS se necessário
        }))
    password = forms.CharField(label='Senha', widget=forms.PasswordInput(attrs={
            'placeholder': 'INSIRA SUA SENHA',
            'class': 'form-control'  # Adicione outras classes CSS se necessário
        }))

    def clean(self):
        ra = self.cleaned_data.get('ra')
        password = self.cleaned_data.get('password')
       
        if ra and password:         
            self.user_cache = authenticate(ra=ra, password=password)
            if self.user_cache is None:
                raise forms.ValidationError('RA ou senha inválidos')
            elif not self.user_cache.is_active:
                raise forms.ValidationError('Esta conta está inativa')
        return self.cleaned_data

    def get_user(self):
        return self.user_cache