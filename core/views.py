from django.shortcuts import render, redirect, get_object_or_404
from .models import Solicitacao, Arvore
from .forms import SolicitacaoForm, ArvoreForm


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
    
def arvore_list(request):
    arvores = Arvore.objects.all()
    return render(request, 'core/arvore_list.html', {'arvores': arvores})

def arvore_create(request):
    if request.method == 'POST':
        form = ArvoreForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('arvore_list')
    else:
        form = ArvoreForm()
    return render(request, 'core/arvore_form.html', {'form': form})

def arvore_update(request, pk):
    arvore = get_object_or_404(Arvore, pk=pk)
    if request.method == 'POST':
        form = ArvoreForm(request.POST, instance=arvore)
        if form.is_valid():
            form.save()
            return redirect('arvore_list')
    else:
        form = ArvoreForm(instance=arvore)
    return render(request, 'core/arvore_form.html', {'form': form})

def mapa_view(request):
    return render(request, 'core/mapa.html')