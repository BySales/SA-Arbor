from django import forms
from .models import Solicitacao, Arvore, Area

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