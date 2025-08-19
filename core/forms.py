from django import forms
from .models import Solicitacao, Arvore

class SolicitacaoForm(forms.ModelForm):
    class Meta:
        model = Solicitacao
        fields = ['tipo', 'descricao']

class ArvoreForm(forms.ModelForm):
    class Meta:
        model = Arvore
        fields = ['nome_popular', 'nome_cientifico', 'descricao']