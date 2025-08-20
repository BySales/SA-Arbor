import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Solicitacao, Arvore, Projeto, Area
from .forms import SolicitacaoForm, ArvoreForm
from django.contrib.auth.forms import UserCreationForm

# --- VIEWS DE SOLICITAÇÃO ---

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
        form = SolicitacaoForm(request.POST, instance=solicitacao)
        if form.is_valid():
            form.save()
            return redirect('solicitacao_list')
    else:
        form = SolicitacaoForm(instance=solicitacao)
    return render(request, 'core/solicitacao_form.html', {'form': form})

# --- VIEWS DE ÁRVORE ---

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

# --- VIEW DO MAPA ---

def mapa_view(request):
    arvores_com_coords = Arvore.objects.filter(latitude__isnull=False, longitude__isnull=False)
    arvores_data = [
        {"nome": arvore.nome_popular, "lat": arvore.latitude, "lon": arvore.longitude} 
        for arvore in arvores_com_coords
    ]

    solicitacoes_com_coords = Solicitacao.objects.filter(status='ABERTO', latitude__isnull=False, longitude__isnull=False)
    solicitacoes_data = [
        {"tipo": solicitacao.get_tipo_display(), "lat": solicitacao.latitude, "lon": solicitacao.longitude}
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