import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Solicitacao, Arvore, Projeto, Area
from django.contrib.auth.forms import UserCreationForm
from .forms import SolicitacaoForm, ArvoreForm


# --- VIEWS DE SOLICITAÇÃO ---


@login_required # Vamos garantir que só usuários logados vejam a home
def solicitacao_list(request):
    # --- LÓGICA DE FILTRO POR USUÁRIO ---
    if request.user.is_superuser or request.user.is_staff:
        # Se for admin ou um "gestor", mostra tudo
        solicitacoes = Solicitacao.objects.all()
    else:
        # Se for usuário comum, mostra apenas as solicitações criadas por ele
        solicitacoes = Solicitacao.objects.filter(cidadao=request.user)

    # --- A lógica do Dashboard continua a mesma, mas usando a lista já filtrada ---
    abertas_count = solicitacoes.filter(status='EM_ABERTO').count()
    andamento_count = solicitacoes.filter(status='EM_ANDAMENTO').count()
    finalizadas_count = solicitacoes.filter(status='FINALIZADO').count()

    context = {
        'solicitacoes': solicitacoes,
        'abertas_count': abertas_count,
        'andamento_count': andamento_count,
        'finalizadas_count': finalizadas_count,
    }
    return render(request, 'core/solicitacao_list.html', context)

@login_required
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

@login_required
def solicitacao_update(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)
    if request.method == 'POST':
        form = SolicitacaoForm(request.POST, instance=solicitacao)
        if form.is_valid():
            form.save()
            return redirect('solicitacao_list')
    else:
        form = SolicitacaoForm(instance=solicitacao)
    return render(request, 'core/solicitacao_form.html', {'form': form})

@login_required
def solicitacao_delete(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)
    if request.method == 'POST': 
        solicitacao.delete()
        return redirect('solicitacao_list')
    return render(request, 'core/solicitacao_confirm_delete.html', {'object': solicitacao})

# --- VIEWS DE ÁRVORE ---

def arvore_list(request):
    arvores = Arvore.objects.all()
    return render(request, 'core/arvore_list.html', {'arvores': arvores})

@login_required
def arvore_create(request):
    if request.method == 'POST':
        form = ArvoreForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('arvore_list')
    else:
        form = ArvoreForm()
    return render(request, 'core/arvore_form.html', {'form': form})

@login_required
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

# Arquivo: core/views.py

@login_required
def arvore_delete(request, pk):
    arvore = get_object_or_404(Arvore, pk=pk)
    if request.method == 'POST':
        arvore.delete()
        return redirect('arvore_list')
    return render(request, 'core/arvore_confirm_delete.html', {'object': arvore})

# --- VIEW DO MAPA ---

# Arquivo: core/views.py

def mapa_view(request):
    arvores_com_coords = Arvore.objects.filter(latitude__isnull=False, longitude__isnull=False)
    arvores_data = [
        {"nome": arvore.nome_popular, "lat": arvore.latitude, "lon": arvore.longitude} 
        for arvore in arvores_com_coords
    ]

    solicitacoes_com_coords = Solicitacao.objects.filter(status='EM_ABERTO', latitude__isnull=False, longitude__isnull=False)
    solicitacoes_data = [
        {
            # A MUDANÇA ESTÁ AQUI: Mandamos o nome bonito E o código interno
            "tipo_display": solicitacao.get_tipo_display(),
            "tipo_codigo": solicitacao.tipo, # Ex: 'SUGESTAO' ou 'DENUNCIA'
            "lat": solicitacao.latitude,
            "lon": solicitacao.longitude
        }
        for solicitacao in solicitacoes_com_coords
    ]

    areas_salvas = Area.objects.filter(geom__isnull=False)
    areas_data = [
        {"nome": area.nome, "geom": area.geom}
        for area in areas_salvas
    ]

    context = {
        'arvores_data': arvores_data,
        'solicitacoes_data': solicitacoes_data,
        'areas_data': areas_data,
    }
    return render(request, 'core/mapa.html', context)

# --- API PARA SALVAR ÁREA ---

@csrf_exempt
@login_required
def salvar_area(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        primeiro_projeto = Projeto.objects.first()
        if not primeiro_projeto:
            return JsonResponse({'status': 'erro', 'message': 'Nenhum projeto encontrado para associar a área.'}, status=400)

        nova_area = Area.objects.create(
            geom=data.get('geometry'),
            nome="Área Desenhada via Mapa",
            projeto=primeiro_projeto,
            status='PLANEJANDO',
            tipo='PUBLICA',
            tipo_vegetacao='NENHUMA'
        )
        
        return JsonResponse({'status': 'ok', 'message': 'Área salva com sucesso!', 'id': nova_area.id})
    
    return JsonResponse({'status': 'erro', 'message': 'Método não permitido'}, status=405)

def cadastro_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, 'core/cadastro.html', {'form': form})