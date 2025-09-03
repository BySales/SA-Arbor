import json
from datetime import date, timedelta
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import Solicitacao, Projeto, Area, User, Equipe, Especie, InstanciaArvore 
from .forms import SolicitacaoForm, AreaForm, UserUpdateForm, ProfileUpdateForm, EquipeForm, EspecieForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from datetime import datetime


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
    recusadas_count = dashboard_qs.filter(status='RECUSADO').count()

    context = {
        'solicitacoes': solicitacoes,
        'abertas_count': abertas_count,
        'andamento_count': andamento_count,
        'finalizadas_count': finalizadas_count,
        'recusadas_count': recusadas_count,
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

@login_required
def especie_list(request):
    especies = Especie.objects.all()
    # Trocamos 'arvore_list.html' por 'especie_list.html'
    return render(request, 'core/especie_list.html', {'especies': especies})

@login_required
def especie_create(request):
    if request.method == 'POST':
        form = EspecieForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nova espécie cadastrada no catálogo!')
            return redirect('especie_list')
    else:
        form = EspecieForm()
    # Trocamos 'arvore_form.html' por 'especie_form.html'
    return render(request, 'core/especie_form.html', {'form': form, 'titulo': 'Cadastrar Nova Espécie'})

@login_required
def especie_update(request, pk):
    especie = get_object_or_404(Especie, pk=pk)
    if request.method == 'POST':
        form = EspecieForm(request.POST, instance=especie)
        if form.is_valid():
            form.save()
            messages.success(request, f'Espécie "{especie.nome_popular}" foi atualizada.')
            return redirect('especie_list')
    else:
        form = EspecieForm(instance=especie)
    return render(request, 'core/especie_form.html', {'form': form, 'titulo': f'Editar Espécie: {especie.nome_popular}'})

@login_required
def especie_delete(request, pk):
    especie = get_object_or_404(Especie, pk=pk)
    if request.method == 'POST':
        try:
            nome_especie = especie.nome_popular
            especie.delete()
            messages.success(request, f'Espécie "{nome_especie}" foi deletada do catálogo.')
        except Exception as e:
            messages.error(request, f'Não foi possível deletar a espécie "{especie.nome_popular}", pois ela já está sendo utilizada em árvores no mapa.')
        return redirect('especie_list')
    return render(request, 'core/especie_confirm_delete.html', {'object': especie})

# --- VIEW DO MAPA ---

def mapa_view(request):
    instancias_de_arvores = InstanciaArvore.objects.select_related('especie').all()
    arvores_data = [
        {
            "id": instancia.id, 
            "nome": instancia.especie.nome_popular, 
            "nome_cientifico": instancia.especie.nome_cientifico,
            "descricao": instancia.especie.descricao,
            "lat": instancia.latitude, 
            "lon": instancia.longitude,
            "saude": instancia.get_estado_saude_display(),
            "plantio": instancia.data_plantio.strftime('%d/%m/%Y') if instancia.data_plantio else 'N/A'
        } 
        for instancia in instancias_de_arvores
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

    todas_especies = Especie.objects.all()
    opcoes_saude = InstanciaArvore.ESTADO_SAUDE_CHOICES

    context = {
        'arvores_data': arvores_data,
        'solicitacoes_data': solicitacoes_data,
        'areas_data': areas_data,
        'form_area': form_area,
        'todas_especies': todas_especies,
        'opcoes_saude': opcoes_saude,
    }
    return render(request, 'core/mapa.html', context)

@csrf_exempt
@login_required
def instancia_arvore_create_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            especie_id = data.get('especie_id')
            lat = data.get('lat')
            lon = data.get('lon')
            estado_saude = data.get('estado_saude')
            data_plantio_str = data.get('data_plantio') # Pegamos a data como texto

            if not all([especie_id, lat, lon]):
                return JsonResponse({'status': 'erro', 'message': 'Dados incompletos.'}, status=400)

            # --- CORREÇÃO AQUI ---
            # Convertemos o texto da data para um objeto de data do Python
            # Se o texto estiver vazio, a data fica como None (nula)
            data_plantio_obj = None
            if data_plantio_str:
                data_plantio_obj = datetime.strptime(data_plantio_str, '%Y-%m-%d').date()

            especie = get_object_or_404(Especie, id=especie_id)
            
            nova_instancia = InstanciaArvore.objects.create(
                especie=especie,
                latitude=lat,
                longitude=lon,
                estado_saude=estado_saude,
                data_plantio=data_plantio_obj # Usamos o objeto de data já convertido
            )

            nova_arvore_data = {
                "id": nova_instancia.id,
                "nome": nova_instancia.especie.nome_popular,
                "nome_cientifico": nova_instancia.especie.nome_cientifico,
                "descricao": nova_instancia.especie.descricao,
                "lat": nova_instancia.latitude,
                "lon": nova_instancia.longitude,
                "saude": nova_instancia.get_estado_saude_display(),
                "plantio": nova_instancia.data_plantio.strftime('%d/%m/%Y') if nova_instancia.data_plantio else 'N/A'
            }

            return JsonResponse({'status': 'ok', 'message': 'Árvore adicionada com sucesso!', 'nova_arvore': nova_arvore_data})
        
        except Exception as e:
            return JsonResponse({'status': 'erro', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'erro', 'message': 'Método não permitido'}, status=405)

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


