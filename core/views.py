import json
from datetime import date, timedelta
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import Solicitacao, Arvore, Projeto, Area, User, Equipe
from .forms import SolicitacaoForm, ArvoreForm, AreaForm, UserUpdateForm, ProfileUpdateForm, EquipeForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash


# --- VIEWS DE SOLICITAÇÃO ---

@login_required
def solicitacao_list(request):
    periodo = request.GET.get('periodo', 'total')
    status = request.GET.get('status')
    ordenar = request.GET.get('ordenar')

    # Queryset base, começando com tudo
    solicitacoes_base = Solicitacao.objects.all()

    # 1. Filtra por status, se ele for passado na URL
    if status:
        solicitacoes_base = solicitacoes_base.filter(status=status)

    # Base para os cards do dashboard (só com filtro de período)
    dashboard_qs = Solicitacao.objects.all()
    if periodo == 'hoje':
        dashboard_qs = dashboard_qs.filter(data_criacao__date=date.today())
    elif periodo == 'semana':
        uma_semana_atras = date.today() - timedelta(days=7)
        dashboard_qs = dashboard_qs.filter(data_criacao__date__gte=uma_semana_atras)
    elif periodo == 'mes':
        um_mes_atras = date.today() - timedelta(days=30)
        dashboard_qs = dashboard_qs.filter(data_criacao__date__gte=um_mes_atras)

    # 2. Filtra a lista principal por período
    solicitacoes_filtradas = solicitacoes_base
    if periodo == 'hoje':
        solicitacoes_filtradas = solicitacoes_base.filter(data_criacao__date=date.today())
    elif periodo == 'semana':
        uma_semana_atras = date.today() - timedelta(days=7)
        solicitacoes_filtradas = solicitacoes_base.filter(data_criacao__date__gte=uma_semana_atras)
    elif periodo == 'mes':
        um_mes_atras = date.today() - timedelta(days=30)
        solicitacoes_filtradas = solicitacoes_base.filter(data_criacao__date__gte=um_mes_atras)

    # 3. Filtra por usuário (cidadão comum só vê o dele)
    if request.user.is_superuser or request.user.is_staff:
        solicitacoes = solicitacoes_filtradas
    else:
        solicitacoes = solicitacoes_filtradas.filter(cidadao=request.user)

    # 4. Ordena o resultado final
    if ordenar == 'data_asc':
        solicitacoes = solicitacoes.order_by('data_criacao')
    elif ordenar == 'tipo':
        solicitacoes = solicitacoes.order_by('tipo')
    else: # A ordem padrão é por mais recente
        solicitacoes = solicitacoes.order_by('-data_criacao')

    # A contagem dos cards do topo usa o filtro de período, mas ignora o de status
    abertas_count = dashboard_qs.filter(status='EM_ABERTO').count()
    andamento_count = dashboard_qs.filter(status='EM_ANDAMENTO').count()
    finalizadas_count = dashboard_qs.filter(status='FINALIZADO').count()

    context = {
        'solicitacoes': solicitacoes,
        'abertas_count': abertas_count,
        'andamento_count': andamento_count,
        'finalizadas_count': finalizadas_count,
        'periodo_selecionado': periodo,
        'status_selecionado': status, # Manda o status pra saber qual tá ativo
        'ordenar_selecionado': ordenar, # Manda a ordenação pra saber qual tá ativa
    }
    return render(request, 'core/solicitacao_list.html', context)

# O resto do arquivo continua igual...
@login_required
def solicitacao_create(request):
    if request.method == 'POST':
        form = SolicitacaoForm(request.POST, request.FILES)
        if form.is_valid():
            solicitacao = form.save(commit=False)
            solicitacao.cidadao = request.user
            solicitacao.save()
            messages.success(request, 'Solicitação criada com sucesso!')
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
            messages.success(request, f'Solicitação #{solicitacao.id} foi atualizada com sucesso!')
            return redirect('solicitacao_list')
    else:
        form = SolicitacaoForm(instance=solicitacao)
    return render(request, 'core/solicitacao_form.html', {'form': form})

@login_required
def solicitacao_delete(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)
    if request.method == 'POST':
        id_solicitacao = solicitacao.id
        solicitacao.delete()
        messages.success(request, f'Solicitação #{id_solicitacao} foi deletada com sucesso!')
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

@login_required
def configuracoes_view(request):
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
            
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Seu perfil foi atualizado com sucesso!')
                return redirect('configuracoes')
            else:
                password_form = PasswordChangeForm(request.user)

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            user_form = UserUpdateForm(instance=request.user)
            profile_form = ProfileUpdateForm(instance=request.user.profile)

            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Sua senha foi alterada com sucesso!')
                return redirect('configuracoes')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
        password_form = PasswordChangeForm(request.user)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form
    }
    return render(request, 'core/configuracoes.html', context)

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
    
@login_required
def equipe_list(request):
    equipes = Equipe.objects.all()
    return render(request, 'core/equipe_list.html', {'equipes': equipes})

@login_required
def equipe_create(request):
    if request.method == 'POST':
        form = EquipeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Equipe criada com sucesso!')
            return redirect('equipe_list')
    else:
        form = EquipeForm()
    return render(request, 'core/equipe_form.html', {'form': form, 'titulo': 'Cadastrar Nova Equipe'})

@login_required
def equipe_update(request, pk):
    equipe = get_object_or_404(Equipe, pk=pk)
    if request.method == 'POST':
        form = EquipeForm(request.POST, instance=equipe)
        if form.is_valid():
            form.save()
        messages.success(request, f'Equipe "{equipe.nome}" foi atualizada com sucesso!')
        return redirect('equipe_list')
    else:
        form = EquipeForm(instance=equipe)
    return render(request, 'core/equipe_form.html', {'form': form, 'titulo': f'Editar Equipe: {equipe.nome}'})

@login_required
def equipe_delete(request, pk):
    equipe = get_object_or_404(Equipe, pk=pk)
    if request.method == 'POST':
        nome_equipe = equipe.nome
        equipe.delete()
        messages.success(request, f'Equipe "{nome_equipe}" foi deletada com sucesso!')
        return redirect('equipe_list')
    return render(request, 'core/equipe_confirm_delete.html', {'object': equipe})


