from django.shortcuts import render, redirect, get_object_or_404
from .models import Solicitacao
from .forms import SolicitacaoForm 


def solicitacao_list(request):
    solicitacoes = Solicitacao.objects.all()
    return render(request, 'core/solicitacao_list.html', {'solicitacoes': solicitacoes})



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

def solicitacao_update(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('solicitacao_list')
    else:
        form = SolicitacaoForm(instance=solicitacao)
        return render(request, 'core/solicitacao_form.html', {'form': form})