from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import Solicitacao, Area, Profile, Equipe, Especie, Tag# Adicionamos o Profile aqui

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
        # 1. Adicionamos os novos campos na lista
        fields = ['nome_popular', 'nome_cientifico', 'descricao', 'imagem', 'tags']
        
        # 2. Adicionamos os labels para os novos campos
        labels = {
            'nome_popular': 'Nome Popular',
            'nome_cientifico': 'Nome Científico',
            'descricao': 'Descrição da Espécie',
            'imagem': 'Foto da Espécie',
            'tags': 'Tags (Categorias)',
        }

        # 3. Definimos os widgets (a aparência) de cada campo
        widgets = {
            'nome_popular': forms.TextInput(attrs={
                'class': 'form-control-custom', 
                'autocomplete': 'off'
            }),
            'nome_cientifico': forms.TextInput(attrs={
                'class': 'form-control-custom', 
                'autocomplete': 'off'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control-custom', 
                'autocomplete': 'off', 
                'rows': 4
            }),
            # Widget especial para o campo de imagem (escondemos o input padrão)
            'imagem': forms.ClearableFileInput(attrs={'class': 'd-none'}),
            
            # Widget que transforma a seleção de tags em checkboxes
            'tags': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
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
    class Meta:
        model = User
        # Adicionamos o username pra ele aparecer na tela, mas não ser editável
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': 'Nome de Usuário (não pode ser alterado)',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'Email de Contato',
        }
        widgets = {
            # Deixamos o username apenas como leitura (readonly) por segurança
            'username': forms.TextInput(attrs={'class': 'form-control-custom', 'readonly': True}),
            'first_name': forms.TextInput(attrs={'class': 'form-control-custom', 'autocomplete': 'off'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control-custom', 'autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'class': 'form-control-custom', 'autocomplete': 'off'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['imagem']
        labels = {
            'imagem': 'Alterar foto de perfil'
        }
        widgets = {
            # Adicionamos a classe aqui também para manter o padrão
            'imagem': forms.FileInput(attrs={'class': 'form-control-custom'}),
        }
class EquipeForm(forms.ModelForm):
    class Meta:
        model = Equipe
        fields = ['nome', 'membros']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control-custom', 'autocomplete': 'off'}),
            # Checkbox não precisa da classe form-control, o Bootstrap já estiliza ele bem
            'membros':forms.CheckboxSelectMultiple,
        }