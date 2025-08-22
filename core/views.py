import json
from datetime import date, timedelta
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from .models import Solicitacao, Arvore, Projeto, Area, User
from .forms import SolicitacaoForm, ArvoreForm, AreaForm

# --- VIEWS DE SOLICITAÇÃO ---

@login_required
def solicitacao_list(request):
    periodo = request.GET.get('periodo', 'total')
    solicitacoes_base = Solicitacao.objects.all()
    if periodo == 'hoje':
        solicitacoes_filtradas = solicitacoes_base.filter(data_criacao__date=date.today())
    elif periodo == 'semana':
        uma_semana_atras = date.today() - timedelta(days=7)
        solicitacoes_filtradas = solicitacoes_base.filter(data_criacao__date__gte=uma_semana_atras)
    elif periodo == 'mes':
        um_mes_atras = date.today() - timedelta(days=30)
        solicitacoes_filtradas = solicitacoes_base.filter(data_criacao__date__gte=um_mes_atras)
    else:
        solicitacoes_filtradas = solicitacoes_base
    if request.user.is_superuser or request.user.is_staff:
        solicitacoes = solicitacoes_filtradas
    else:
        solicitacoes = solicitacoes_filtradas.filter(cidadao=request.user)
    abertas_count = solicitacoes.filter(status='EM_ABERTO').count()
    andamento_count = solicitacoes.filter(status='EM_ANDAMENTO').count()
    finalizadas_count = solicitacoes.filter(status='FINALIZADO').count()
    context = {
        'solicitacoes': solicitacoes,
        'abertas_count': abertas_count,
        'andamento_count': andamento_count,
        'finalizadas_count': finalizadas_count,
        'periodo_selecionado': periodo,
    }
    return render(request, 'core/solicitacao_list.html', context)

@login_required
def solicitacao_create(request):
    if request.method == 'POST':
        form = SolicitacaoForm(request.POST, request.FILES)
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
        form = SolicitacaoForm(request.POST, request.FILES, instance=solicitacao)
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

@login_required
def arvore_delete(request, pk):
    arvore = get_object_or_404(Arvore, pk=pk)
    if request.method == 'POST':
        arvore.delete()
        return redirect('arvore_list')
    return render(request, 'core/arvore_confirm_delete.html', {'object': arvore})

# --- VIEW DO MAPA ---

def mapa_view(request):
    arvores_com_coords = Arvore.objects.filter(latitude__isnull=False, longitude__isnull=False)
    arvores_data = [
        {"id": arvore.id, "nome": arvore.nome_popular, "nome_cientifico": arvore.nome_cientifico, "descricao": arvore.descricao, "lat": arvore.latitude, "lon": arvore.longitude} 
        for arvore in arvores_com_coords
    ]
    solicitacoes_com_coords = Solicitacao.objects.filter(status='EM_ABERTO', latitude__isnull=False, longitude__isnull=False)
    solicitacoes_data = [
        {"id": solicitacao.id, "tipo_display": solicitacao.get_tipo_display(), "tipo_codigo": solicitacao.tipo, "status": solicitacao.status, "descricao": solicitacao.descricao, "lat": solicitacao.latitude, "lon": solicitacao.longitude}
        for solicitacao in solicitacoes_com_coords
    ]
    areas_salvas = Area.objects.filter(geom__isnull=False)
    areas_data = [
        {"id": area.id, "nome": area.nome, "geom": area.geom, "tipo": area.get_tipo_display(), "status": area.get_status_display()}
        for area in areas_salvas
    ]
    form_area = AreaForm()
    context = {
        'arvores_data': arvores_data,
        'solicitacoes_data': solicitacoes_data,
        'areas_data': areas_data,
        'form_area': form_area,
    }
    return render(request, 'core/mapa.html', context)

# --- VIEWS DE AUTENTICAÇÃO E API ---

def cadastro_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'core/cadastro.html', {'form': form})

@csrf_exempt
@login_required
def salvar_area(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        form_data = data.get('form_data')
        geometry_data = data.get('geometry')
        if not form_data or not geometry_data:
            return JsonResponse({'status': 'erro', 'message': 'Dados incompletos.'}, status=400)
        form = AreaForm(form_data)
        if form.is_valid():
            area = form.save(commit=False)
            area.geom = geometry_data
            area.projeto = Projeto.objects.first()
            area.save()
            form.save_m2m()
            return JsonResponse({'status': 'ok', 'message': 'Área salva com sucesso!', 'id': area.id})
        else:
            return JsonResponse({'status': 'erro', 'message': 'Dados do formulário inválidos.', 'errors': form.errors.as_json()}, status=400)
    return JsonResponse({'status': 'erro', 'message': 'Método não permitido'}, status=405)

# --- (NOVA) API PARA GERENCIAR UMA ÁREA ESPECÍFICA ---
@csrf_exempt
@login_required
def area_manage_api(request, pk):
    area = get_object_or_404(Area, pk=pk)

    # SE A REQUISIÇÃO FOR PARA ATUALIZAR (PUT)
    if request.method == 'PUT':
        data = json.loads(request.body)
        form_data = data.get('form_data')
        form = AreaForm(form_data, instance=area)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'ok', 'message': 'Área atualizada com sucesso!'})
        else:
            return JsonResponse({'status': 'erro', 'errors': form.errors.as_json()}, status=400)

    # SE A REQUISIÇÃO FOR PARA DELETAR (DELETE)
    elif request.method == 'DELETE':
        area.delete()
        return JsonResponse({'status': 'ok', 'message': 'Área deletada com sucesso!'})
    
    # SE A REQUISIÇÃO FOR PARA PEGAR OS DETALHES (GET)
    else: # GET
        data = {
            'id': area.id,
            'nome': area.nome,
            'tipo': area.tipo,
            'status': area.status,
            'responsavel': area.responsavel.id if area.responsavel else '',
            'tipo_vegetacao': area.tipo_vegetacao,
            'especies': list(area.especies.all().values_list('id', flat=True))
        }
        return JsonResponse(data)