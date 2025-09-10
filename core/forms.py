from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import Solicitacao, Area, Profile, Equipe, Especie# Adicionamos o Profile aqui

class SolicitacaoForm(forms.ModelForm):
    imagens = forms.ImageField(
        required=False,
        label='Anexar imagens (segure CTRL para selecionar várias)'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['imagens'].widget.attrs.update({'multiple': True})

    class Meta:
        model = Solicitacao
        fields = ['tipo', 'descricao', 'latitude', 'longitude', 'status', 'equipe_delegada']
        
        # A MÁGICA ESTÁ AQUI: definindo o estilo de cada campo
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select form-control-custom'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control form-control-custom', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select form-control-custom'}),
            'equipe_delegada': forms.Select(attrs={'class': 'form-select form-control-custom'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
        
        labels = {
            'tipo': 'Tipo',
            'descricao': 'Descrição',
            'status': 'Status da Solicitação',
            'equipe_delegada': 'Delegar para a Equipe',
            'imagens': 'Anexar imagens (segure CTRL para selecionar várias)'
        }

class EspecieForm(forms.ModelForm):
    class Meta:
        model = Especie
        fields = ['nome_popular', 'nome_cientifico', 'descricao']
        labels = {
            'nome_popular': 'Nome Popular',
            'nome_cientifico': 'Nome Científico',
            'descricao': 'Descrição',
        }
        widgets = {
            'nome_popular': forms.TextInput(attrs={
                'class': 'form-control form-control-custom', 
                'autocomplete': 'off'
            }),
            'nome_cientifico': forms.TextInput(attrs={
                'class': 'form-control form-control-custom', 
                'autocomplete': 'off'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control form-control-custom', 
                'autocomplete': 'off', 
                'rows': 4
            }),
        }

class AreaForm(forms.ModelForm):
    class Meta: 
        model = Area
        # Agora só pede os campos que realmente existem no formulário do mapa
        fields = ['nome', 'tipo', 'status', 'especies']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'autocomplete': 'off'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select form-control-custom'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select form-control-custom'
            }),
            'especies': forms.SelectMultiple(attrs={
                'class': 'form-select form-control-custom select2-multiple', 
                'style': 'width: 100%;'
            }),
        }
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'autocomplete': 'off'}),
            'last_name': forms.TextInput(attrs={'autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'off'}),
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

class EquipeForm(forms.ModelForm):
    class Meta:
        model = Equipe
        fields = ['nome', 'membros']
        widgets = {
            'nome': forms.TextInput(attrs={'autocomplete': 'off'}),
            'membros':forms.CheckboxSelectMultiple,
        }