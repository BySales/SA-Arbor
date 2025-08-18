from django.shortcuts import render
from .models import Solicitacao
from .forms import SolicitacaoForm

# Create your views here.

def solicitacao_list(request):
    solicitacoes = Solicitacao.objects.all()
    return render(request, 'core/solicitacao_list.html', {'solicitacoes': solicitacoes})

from django.shortcuts import render, redirect # 1. Adiciona o 'redirect'
from .models import Solicitacao
from .forms import SolicitacaoForm # 2. Importa nossa "comanda inteligente"

# ... a função solicitacao_list continua aqui em cima ...
def solicitacao_list(request):
    solicitacoes = Solicitacao.objects.all()
    return render(request, 'core/solicitacao_list.html', {'solicitacoes': solicitacoes})



def solicitacao_create(request):
    if request.method == 'POST':
        form = SolicitacaoForm(request.POST)
        if form.is_valid():
            solicitacao = form.save(commit=False)
            solicitacao.cidadao = request.user
            solicitacao.save()
            return redirect('solicitacao_list')
    else:
        form = SolicitacaoForm()
    return render(request, 'core/solicitacao_form.html', {'form': form})