from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import Solicitacao, Area, Profile, Equipe, Especie# Adicionamos o Profile aqui

class SolicitacaoForm(forms.ModelForm):
    # 1. A gente define o campo de imagens de forma mais simples aqui
    imagens = forms.ImageField(
        required=False,
        # O widget agora é definido depois, então não precisa colocar aqui
        label='Anexar imagens (segure CTRL para selecionar várias)'
    )

    # 2. A MÁGICA ACONTECE AQUI, no construtor do formulário
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A gente acessa o widget do campo 'imagens' DEPOIS que ele foi criado
        # e adiciona o atributo 'multiple' na marra.
        self.fields['imagens'].widget.attrs.update({'multiple': True})

    class Meta:
        model = Solicitacao
        fields = ['tipo', 'descricao', 'latitude', 'longitude', 'status', 'equipe_delegada']
        widgets = {
            'descricao': forms.Textarea(attrs={'autocomplete': 'off', 'rows': 4}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
        labels = {
            'status': 'Status da Solicitação',
            'equipe_delegada': 'Delegar para a Equipe'
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
            'nome_popular': forms.TextInput(attrs={'autocomplete': 'off'}),
            'nome_cientifico': forms.TextInput(attrs={'autocomplete': 'off'}),
            'descricao': forms.Textarea(attrs={'autocomplete': 'off', 'rows': 4}),
        }

class AreaForm(forms.ModelForm):
    class Meta: 
        model = Area
        fields = ['nome', 'tipo', 'status', 'responsavel', 'tipo_vegetacao', 'especies']
        widgets = {
            'nome': forms.TextInput(attrs={'autocomplete': 'off'}),
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