from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import Solicitacao, Arvore, Area, Profile # Adicionamos o Profile aqui

class SolicitacaoForm(forms.ModelForm):
    class Meta:
        model = Solicitacao
        fields = ['tipo', 'descricao', 'latitude', 'longitude', 'imagem']

class ArvoreForm(forms.ModelForm):
    class Meta:
        model = Arvore
        fields = ['nome_popular', 'nome_cientifico', 'descricao']


class AreaForm(forms.ModelForm):
    class Meta: 
        model = Area
        fields = ['nome', 'tipo', 'status', 'responsavel', 'tipo_vegetacao', 'especies']

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['imagem']
        widgets = {
            'imagem': forms.FileInput,
        }
        labels = {
            'imagem': 'Alterar foto de perfil'
        }