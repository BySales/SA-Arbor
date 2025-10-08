import json
from datetime import date, timedelta, datetime
from django.http import JsonResponse
# IMPORTS ADICIONADOS AQUI
from django.urls import reverse
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
# FIM DOS IMPORTS ADICIONADOS
from django.views.decorators.http import require_http_methods
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import Solicitacao, Projeto, Area, User, Equipe, Especie, InstanciaArvore, ImagemSolicitacao,TagCategory, Tag
from .forms import SolicitacaoForm, AreaForm, UserUpdateForm, ProfileUpdateForm, EquipeForm, EspecieForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.db.models.functions import TruncMonth
from .models import Profile



# --- VIEWS DE SOLICITAÇÃO ---

@login_required
def solicitacao_list(request):
    periodo = request.GET.get('periodo', 'total')
    status = request.GET.get('status')
    ordenar = request.GET.get('ordenar')

    # --- Lógica de Filtros ---
    solicitacoes_base = Solicitacao.objects.all()
    if status:
        solicitacoes_base = solicitacoes_base.filter(status=status)

    dashboard_qs = Solicitacao.objects.all()
    if periodo == 'hoje':
        dashboard_qs = dashboard_qs.filter(data_criacao__date=date.today())
    elif periodo == 'semana':
        uma_semana_atras = date.today() - timedelta(days=7)
        dashboard_qs = dashboard_qs.filter(data_criacao__date__gte=uma_semana_atras)
    elif periodo == 'mes':
        um_mes_atras = date.today() - timedelta(days=30)
        dashboard_qs = dashboard_qs.filter(data_criacao__date__gte=um_mes_atras)

    solicitacoes_filtradas = solicitacoes_base
    if periodo == 'hoje':
        solicitacoes_filtradas = solicitacoes_base.filter(data_criacao__date=date.today())
    elif periodo == 'semana':
        uma_semana_atras = date.today() - timedelta(days=7)
        solicitacoes_filtradas = solicitacoes_base.filter(data_criacao__date__gte=uma_semana_atras)
    elif periodo == 'mes':
        um_mes_atras = date.today() - timedelta(days=30)
        solicitacoes_filtradas = solicitacoes_base.filter(data_criacao__date__gte=um_mes_atras)

    # --- CORREÇÃO AQUI: Garantindo que 'solicitacoes' seja definida ---
    if request.user.is_superuser or request.user.is_staff:
        solicitacoes_query = solicitacoes_filtradas
    else:
        solicitacoes_query = solicitacoes_filtradas.filter(cidadao=request.user)

    if ordenar == 'data_asc':
        solicitacoes_ordenadas = solicitacoes_query.order_by('data_criacao')
    elif ordenar == 'tipo':
        solicitacoes_ordenadas = solicitacoes_query.order_by('tipo')
    else:
        solicitacoes_ordenadas = solicitacoes_query.order_by('-data_criacao')

    # --- Paginação ---
    paginator = Paginator(solicitacoes_ordenadas, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # --- Cálculos para o Dashboard ---
    abertas_count = dashboard_qs.filter(status='EM_ABERTO').count()
    andamento_count = dashboard_qs.filter(status='EM_ANDAMENTO').count()
    finalizadas_count = dashboard_qs.filter(status='FINALIZADO').count()
    recusadas_count = dashboard_qs.filter(status='RECUSADO').count()
    
    denuncias_count = dashboard_qs.filter(tipo='DENUNCIA').count()
    sugestoes_count = dashboard_qs.filter(tipo='SUGESTAO').count()

    ultimos_7_dias = [date.today() - timedelta(days=i) for i in range(6, -1, -1)]
    solicitacoes_por_dia = (
        Solicitacao.objects.filter(data_criacao__date__in=ultimos_7_dias)
        .annotate(dia=TruncDate('data_criacao'))
        .values('dia')
        .annotate(total=Count('id'))
        .order_by('dia')
    )
    dados_recente = {dia_obj['dia']: dia_obj['total'] for dia_obj in solicitacoes_por_dia}
    datas_recente_labels = [dia.strftime('%d/%m') for dia in ultimos_7_dias]
    contagem_recente_data = [dados_recente.get(dia, 0) for dia in ultimos_7_dias]

    solicitacoes_em_andamento = Solicitacao.objects.filter(status='EM_ANDAMENTO')
    equipes_data = (
        solicitacoes_em_andamento.exclude(equipe_delegada__isnull=True)
        .values('equipe_delegada__nome')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    equipes_labels = [item['equipe_delegada__nome'] for item in equipes_data]
    equipes_contagem = [item['total'] for item in equipes_data]

    context = {
        'solicitacoes': page_obj,
        'abertas_count': abertas_count,
        'andamento_count': andamento_count,
        'finalizadas_count': finalizadas_count,
        'recusadas_count': recusadas_count,
        'periodo_selecionado': periodo,
        'status_selecionado': status,
        'ordenar_selecionado': ordenar,
        'denuncias_count': denuncias_count,
        'sugestoes_count': sugestoes_count,
        'datas_recente_labels': json.dumps(datas_recente_labels),
        'contagem_recente_data': json.dumps(contagem_recente_data),
        'equipes_labels': json.dumps(equipes_labels),
        'equipes_contagem': json.dumps(equipes_contagem),
    }
    return render(request, 'core/solicitacao_list.html', context)


@login_required
def solicitacao_create(request):
    if request.method == 'POST':
        form = SolicitacaoForm(request.POST) # Não pegamos request.FILES aqui ainda
        
        # A validação agora é feita no JS, mas mantemos uma segurança aqui
        if len(request.FILES.getlist('imagens')) > 10:
            return JsonResponse({'success': False, 'errors': {'imagens': ['Você só pode enviar no máximo 10 imagens.']}}, status=400)

        if form.is_valid():
            solicitacao = form.save(commit=False)
            solicitacao.cidadao = request.user
            solicitacao.save()
            
            # Pega as imagens da "nossa pasta" que o JS mandou
            imagens = request.FILES.getlist('imagens')
            for imagem_file in imagens:
                ImagemSolicitacao.objects.create(solicitacao=solicitacao, imagem=imagem_file)
            
            messages.success(request, 'Solicitação criada com sucesso!')
            # Retorna o recibo de sucesso para o JavaScript
            return JsonResponse({'success': True, 'redirect_url': reverse('solicitacao_list')})
        else:
            # Retorna o recibo de erro com os detalhes
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    # Se for um GET, a lógica continua a mesma
    else:
        form = SolicitacaoForm()
    return render(request, 'core/solicitacao_form.html', {'form': form})


@login_required
def solicitacao_detail(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)
    # Esta view simplesmente pega o objeto e manda para um novo template
    # que vamos criar, o 'solicitacao_detail.html'.
    context = {
        'solicitacao': solicitacao
    }
    return render(request, 'core/solicitacao_detail.html', context)


@login_required
def solicitacao_update(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)
    if request.method == 'POST':
        form = SolicitacaoForm(request.POST, instance=solicitacao) # Não pegamos request.FILES

        # Lógica de validação de contagem de imagens
        imagens_novas = request.FILES.getlist('imagens')
        imagens_atuais_count = solicitacao.imagens.count()
        if (imagens_atuais_count + len(imagens_novas)) > 10:
            error_msg = f'Você não pode ter mais de 10 imagens. Esta solicitação já tem {imagens_atuais_count} e você está tentando adicionar mais {len(imagens_novas)}.'
            return JsonResponse({'success': False, 'errors': {'imagens': [error_msg]}}, status=400)

        if form.is_valid():
            form.save() # Salva os dados do formulário (tipo, descrição, etc)
            
            for imagem_file in imagens_novas:
                ImagemSolicitacao.objects.create(solicitacao=solicitacao, imagem=imagem_file)
            
            messages.success(request, f'Solicitação #{solicitacao.id} foi atualizada com sucesso!')
            # Retorna o recibo de sucesso
            return JsonResponse({'success': True, 'redirect_url': reverse('solicitacao_list')})
        else:
            # Retorna o recibo de erro
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            
    # Se for um GET, a lógica continua a mesma
    else:
        form = SolicitacaoForm(instance=solicitacao)
    context = {
        'form': form,
        'solicitacao': solicitacao 
    }
    return render(request, 'core/solicitacao_form.html', context)

@login_required
def solicitacao_delete(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)
    if request.method == 'POST':
        id_solicitacao = solicitacao.id
        solicitacao.delete()
        messages.success(request, f'Solicitação #{id_solicitacao} foi deletada com sucesso!')
        return redirect('solicitacao_list')
    return render(request, 'core/solicitacao_confirm_delete.html', {'object': solicitacao})


# --- VIEWS DE EQUIPE ---

@login_required
def equipe_list(request):
    equipes_qs = Equipe.objects.prefetch_related('membros').all()
    trinta_dias_atras = timezone.now() - timedelta(days=30)
    
    equipes_com_stats = []
    for equipe in equipes_qs:
        tarefas_ativas = Solicitacao.objects.filter(equipe_delegada=equipe, status='EM_ANDAMENTO').count()
        tarefas_concluidas = Solicitacao.objects.filter(
            equipe_delegada=equipe, 
            status='FINALIZADO',
            # Adicionar um campo de data de finalização no futuro
            # data_finalizacao__gte=trinta_dias_atras 
        ).count()
        
        denuncias_count = Solicitacao.objects.filter(equipe_delegada=equipe, tipo='DENUNCIA').count()
        sugestoes_count = Solicitacao.objects.filter(equipe_delegada=equipe, tipo='SUGESTAO').count()

        equipes_com_stats.append({
            'equipe': equipe,
            'tarefas_ativas': tarefas_ativas,
            'tarefas_concluidas': tarefas_concluidas,
            'denuncias_count': denuncias_count,
            'sugestoes_count': sugestoes_count,
        })

    # Pega usuários que são staff mas não estão em nenhuma equipe
    agentes_livres = User.objects.filter(is_staff=True, equipes__isnull=True)

    context = {
        'equipes_com_stats': equipes_com_stats,
        'agentes_livres': agentes_livres,
    }
    return render(request, 'core/equipe_list.html', context)

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


# --- VIEWS DE ESPÉCIE ---

@login_required
def especie_list(request):
    # Esta view já está atualizada e otimizada
    especies = Especie.objects.prefetch_related('tags').order_by('nome_popular')
    paginator = Paginator(especies, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/especie_list.html', {'especies': page_obj})

@login_required
def especie_create(request):
    if request.method == 'POST':
        form = EspecieForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nova espécie cadastrada no catálogo!')
            return redirect('especie_list')
    else:
        form = EspecieForm()
    
    # Buscando as categorias com suas tags relacionadas
    categorias_com_tags = TagCategory.objects.prefetch_related('tags').all()
    
    context = {
        'form': form,
        'titulo': 'Cadastrar Nova Espécie',
        'categorias_com_tags': categorias_com_tags # Mandando para o template
    }
    return render(request, 'core/especie_form.html', context)


@login_required
def especie_update(request, pk):
    especie = get_object_or_404(Especie, pk=pk)
    if request.method == 'POST':
        form = EspecieForm(request.POST, request.FILES, instance=especie)
        if form.is_valid():
            form.save()
            messages.success(request, f'Espécie "{especie.nome_popular}" foi atualizada.')
            return redirect('especie_list')
    else:
        form = EspecieForm(instance=especie)
        
    categorias_com_tags = TagCategory.objects.prefetch_related('tags').all()

    context = {
        'form': form, 
        'titulo': f'Editar Espécie: {especie.nome_popular}',
        'categorias_com_tags': categorias_com_tags
    }
    return render(request, 'core/especie_form.html', context)


@login_required
def especie_delete(request, pk):
    # Esta view não precisa de mudanças
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


# --- VIEWS DE ÁREA (NOVA SEÇÃO) ---

class AreaDeleteView(LoginRequiredMixin, DeleteView):
    model = Area 
    template_name = 'core/area_confirm_delete.html'
    success_url = reverse_lazy('mapa')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Confirmar Deleção de Área'
        return context


# --- VIEW DO MAPA ---

def mapa_view(request):
    solicitacao_foco_id = request.GET.get('solicitacao_id')
    area_foco_id = request.GET.get('area_id')
    instancias_de_arvores = InstanciaArvore.objects.select_related('especie').all()
    arvores_data = [{"id": instancia.id, "nome": instancia.especie.nome_popular, "nome_cientifico": instancia.especie.nome_cientifico, "descricao": instancia.especie.descricao, "lat": instancia.latitude, "lon": instancia.longitude, "saude": instancia.get_estado_saude_display(), "plantio": instancia.data_plantio.strftime('%d/%m/%Y') if instancia.data_plantio else 'N/A'} for instancia in instancias_de_arvores]
    solicitacoes_com_coords = Solicitacao.objects.filter(latitude__isnull=False, longitude__isnull=False)
    solicitacoes_data = [{"id": solicitacao.id, "tipo_display": solicitacao.get_tipo_display(), "tipo_codigo": solicitacao.tipo, "status": solicitacao.get_status_display(), "descricao": solicitacao.descricao, "lat": solicitacao.latitude, "lon": solicitacao.longitude} for solicitacao in solicitacoes_com_coords]
    areas_salvas = Area.objects.filter(geom__isnull=False)
    areas_data = [{"id": area.id, "nome": area.nome, "geom": area.geom, "tipo": area.get_tipo_display(), "status": area.get_status_display()} for area in areas_salvas]
    form_area = AreaForm()
    
    # =======================================================================
    # MUDANÇA 1: Buscando a lista de espécies para o novo modal de árvore
    # =======================================================================
    especies_catalogo = Especie.objects.all().order_by('nome_popular')
    
    opcoes_saude = InstanciaArvore.ESTADO_SAUDE_CHOICES
    
    context = {
        'arvores_data': arvores_data,
        'solicitacoes_data': solicitacoes_data,
        'areas_data': areas_data,
        'form_area': form_area,
        'especies_catalogo': especies_catalogo, # Enviando a lista para o template
        'opcoes_saude': opcoes_saude,
        'solicitacao_foco_id': solicitacao_foco_id,
        'area_foco_id': area_foco_id,
    }
    return render(request, 'core/mapa.html', context)


# --- VIEWS DE AUTENTICAÇÃO E CONFIGURAÇÕES ---

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

def cadastro_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'core/cadastro.html', {'form': form})


# --- API ENDPOINTS ---

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
            # Pega o primeiro projeto ou cria um padrão se não existir nenhum
            projeto, created = Projeto.objects.get_or_create(
                id=1, 
                defaults={'nome': 'Projeto Padrão', 'cidade': 'Mongaguá'}
            )

            area = form.save(commit=False)
            area.geom = geometry_data
            area.projeto = projeto
            area.save()
            form.save_m2m() # Salva as relações ManyToMany (espécies)
            
            return JsonResponse({'status': 'ok', 'message': 'Área salva com sucesso!', 'id': area.id})
        else:
            return JsonResponse({'status': 'erro', 'message': 'Dados do formulário inválidos.', 'errors': form.errors.as_json()}, status=400)
            
    return JsonResponse({'status': 'erro', 'message': 'Método não permitido'}, status=405)

@csrf_exempt
@login_required
def area_manage_api(request, pk):
    area = get_object_or_404(Area, pk=pk)

    if request.method == 'PUT':
        data = json.loads(request.body)
        form_data = data.get('form_data')
        form = AreaForm(form_data, instance=area)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'ok', 'message': 'Área atualizada com sucesso!'})
        else:
            return JsonResponse({'status': 'erro', 'errors': form.errors.as_json()}, status=400)

    elif request.method == 'DELETE':
        area.delete()
        return JsonResponse({'status': 'ok', 'message': 'Área deletada com sucesso!'})
    
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
@require_POST # Garante que esta view só aceite requisições POST
def instancia_arvore_create_api(request):
    try:
        # O formulário com Select2 envia dados como 'form data', não JSON
        especie_id = request.POST.get('especie') 
        lat = request.POST.get('latitude')
        lon = request.POST.get('longitude')
        estado_saude_form = request.POST.get('saude')
        observacoes = request.POST.get('observacoes', '')

        if not all([especie_id, lat, lon]):
            return JsonResponse({'status': 'erro', 'message': 'Dados incompletos.'}, status=400)

        especie_obj = get_object_or_404(Especie, id=especie_id)

        mapa_saude = {'BOA': 'BOA', 'MEDIA': 'REGULAR', 'RUIM': 'RUIM'}
        estado_saude_db = mapa_saude.get(estado_saude_form, 'BOA')

        nova_instancia = InstanciaArvore.objects.create(
            especie=especie_obj,
            latitude=lat,
            longitude=lon,
            estado_saude=estado_saude_db,
            observacoes=observacoes
        )
        return JsonResponse({'status': 'ok', 'message': f'Árvore "{nova_instancia.especie.nome_popular}" adicionada com sucesso!'})
    except Exception as e:
        return JsonResponse({'status': 'erro', 'message': str(e)}, status=500)

def search_results_view(request):
    query = request.GET.get('q')
    context = {'query': query}

    if query:
        # Busca em Solicitações (descrição OU cidadão)
        solicitacoes_results = Solicitacao.objects.filter(
            Q(descricao__icontains=query) | Q(cidadao__username__icontains=query)
        ).distinct()
        context['solicitacoes_results'] = solicitacoes_results

        # Busca em Espécies (nome popular OU científico)
        especies_results = Especie.objects.filter(
            Q(nome_popular__icontains=query) | Q(nome_cientifico__icontains=query)
        ).distinct()
        context['especies_results'] = especies_results

        # Busca em Equipes (nome)
        equipes_results = Equipe.objects.filter(
            Q(nome__icontains=query)
        ).distinct()
        context['equipes_results'] = equipes_results

        # --- A MÁGICA ACONTECE AQUI ---
        # Adiciona o total de resultados ao contexto
        total_results = len(solicitacoes_results) + len(especies_results) + len(equipes_results)
        context['total_results'] = total_results

    # Renderiza o NOVO template com o contexto completo
    return render(request, 'core/search_results.html', context)


# --- VIEW DE OBRAS (KANBAN) ---

@login_required
def obras_view(request):
    arvores = InstanciaArvore.objects.all()

    # Função para contar árvores em uma área
    def contar_arvores_na_area(area):
        if not area.geom:
            return 0
        
        polygon_coords = area.geom['coordinates'][0]
        polygon = [(lat, lon) for lon, lat in polygon_coords]
        
        count = 0
        for arvore in arvores:
            ponto_arvore = (arvore.latitude, arvore.longitude)
            if is_point_in_polygon(ponto_arvore, polygon):
                count += 1
        return count

    # Coluna 1: A Fazer / Planejamento
    solicitacoes_a_fazer = Solicitacao.objects.filter(status='EM_ABERTO').order_by('-data_criacao')
    areas_a_fazer_qs = Area.objects.filter(status__in=['PLANEJANDO', 'AGUARDANDO_APROVAÇAO']).order_by('-data_criacao')
    
    # Adiciona a contagem de árvores a cada área
    areas_a_fazer = []
    for area in areas_a_fazer_qs:
        area.contagem_arvores = contar_arvores_na_area(area)
        areas_a_fazer.append(area)

    # Coluna 2: Em Execução
    solicitacoes_em_execucao = Solicitacao.objects.filter(status='EM_ANDAMENTO').order_by('-data_criacao')
    areas_em_execucao_qs = Area.objects.filter(status='EM_EXECUCAO').order_by('-data_criacao')
    areas_em_execucao = []
    for area in areas_em_execucao_qs:
        area.contagem_arvores = contar_arvores_na_area(area)
        areas_em_execucao.append(area)


    # Coluna 3: Concluídas
    solicitacoes_concluidas = Solicitacao.objects.filter(status='FINALIZADO').order_by('-data_criacao')
    areas_concluidas_qs = Area.objects.filter(status='FINALIZADO').order_by('-data_criacao')
    areas_concluidas = []
    for area in areas_concluidas_qs:
        area.contagem_arvores = contar_arvores_na_area(area)
        areas_concluidas.append(area)

    # A gente calcula o total de cada coluna aqui na view
    count_a_fazer = solicitacoes_a_fazer.count() + len(areas_a_fazer)
    count_em_execucao = solicitacoes_em_execucao.count() + len(areas_em_execucao)
    count_concluido = solicitacoes_concluidas.count() + len(areas_concluidas)

    context = {
        'solicitacoes_a_fazer': solicitacoes_a_fazer,
        'areas_a_fazer': areas_a_fazer,
        'solicitacoes_em_execucao': solicitacoes_em_execucao,
        'areas_em_execucao': areas_em_execucao,
        'solicitacoes_concluidas': solicitacoes_concluidas,
        'areas_concluidas': areas_concluidas,
        
        # E manda os números prontos para o template
        'count_a_fazer': count_a_fazer,
        'count_em_execucao': count_em_execucao,
        'count_concluido': count_concluido,
    }

    return render(request, 'core/obras.html', context)


# --- NOVA API DE ANÁLISE DE ÁREA ---

def is_point_in_polygon(point, polygon):
    """
    Verifica se um ponto (lat, lon) está dentro de um polígono.
    Usa o algoritmo Ray Casting.
    `point` é uma tupla (latitude, longitude).
    `polygon` é uma lista de tuplas [(lat1, lon1), (lat2, lon2), ...].
    """
    lat, lon = point
    n = len(polygon)
    inside = False
    
    p1_lat, p1_lon = polygon[0]
    for i in range(n + 1):
        p2_lat, p2_lon = polygon[i % n]
        if lat > min(p1_lat, p2_lat):
            if lat <= max(p1_lat, p2_lat):
                if lon <= max(p1_lon, p2_lon):
                    if p1_lat != p2_lat:
                        lon_intersection = (lat - p1_lat) * (p2_lon - p1_lon) / (p2_lat - p1_lat) + p1_lon
                    if p1_lon == p2_lon or lon <= lon_intersection:
                        inside = not inside
        p1_lat, p1_lon = p2_lat, p2_lon
        
    return inside


@csrf_exempt
@login_required
def analisar_area_api(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'erro', 'message': 'Método não permitido'}, status=405)

    try:
        data = json.loads(request.body)
        geometry = data.get('geometry')
        if not geometry or 'coordinates' not in geometry:
            return JsonResponse({'status': 'erro', 'message': 'Geometria inválida ou ausente.'}, status=400)
        
        # O GeoJSON formata como (lon, lat), então precisamos pegar a lista de pontos
        polygon_coords = geometry['coordinates'][0]
        # E converter para (lat, lon) para a nossa função
        polygon = [(lat, lon) for lon, lat in polygon_coords]

    except json.JSONDecodeError:
        return JsonResponse({'status': 'erro', 'message': 'JSON mal formatado.'}, status=400)

    # Buscar todos os objetos com coordenadas
    arvores = InstanciaArvore.objects.filter(latitude__isnull=False, longitude__isnull=False)
    solicitacoes = Solicitacao.objects.filter(latitude__isnull=False, longitude__isnull=False)

    # Contadores
    arvores_na_area = 0
    solicitacoes_na_area = 0

    # Testar cada árvore
    for arvore in arvores:
        ponto_arvore = (arvore.latitude, arvore.longitude)
        if is_point_in_polygon(ponto_arvore, polygon):
            arvores_na_area += 1
            
    # Testar cada solicitação
    for solicitacao in solicitacoes:
        ponto_solicitacao = (solicitacao.latitude, solicitacao.longitude)
        if is_point_in_polygon(ponto_solicitacao, polygon):
            solicitacoes_na_area += 1

    return JsonResponse({
        'status': 'ok',
        'contagem_arvores': arvores_na_area,
        'contagem_solicitacoes': solicitacoes_na_area,
    })

def recuperar_senha_view(request):
    # Por enquanto, esta view apenas renderiza o template.
    # A lógica de envio de email e validação de código será adicionada no futuro.
    return render(request, 'core/recuperar_senha.html')

# Adicione esta nova view
@login_required
def home_view(request):
    # Buscando os dados para o nosso dashboard
    instancias_count = InstanciaArvore.objects.count()
    solicitacoes_abertas_count = Solicitacao.objects.filter(status='EM_ABERTO').count()
    equipes_count = Equipe.objects.count()
    especies_count = Especie.objects.count()

    # Pegando as 5 solicitações mais recentes pra mostrar na tela
    ultimas_solicitacoes = Solicitacao.objects.order_by('-data_criacao')[:5]

    context = {
        'instancias_count': instancias_count,
        'solicitacoes_abertas_count': solicitacoes_abertas_count,
        'equipes_count': equipes_count,
        'especies_count': especies_count,
        'ultimas_solicitacoes': ultimas_solicitacoes,
    }
    return render(request, 'core/home.html', context)

@login_required
def relatorios_view(request):
    """
    View para a Central de Relatórios com filtros de período.
    """
    # 1. PEGAR O FILTRO DA URL
    # A gente pega o parâmetro 'periodo'. Se não vier nada, o padrão é 'mes'.
    periodo_selecionado = request.GET.get('periodo', 'mes')

    # 2. CALCULAR A DATA DE INÍCIO BASEADO NO FILTRO
    today = timezone.now().date()
    start_date = None

    if periodo_selecionado == 'semana':
        start_date = today - timedelta(days=7)
    elif periodo_selecionado == 'ano':
        start_date = today.replace(month=1, day=1)
    else: # Padrão é 'mes'
        start_date = today.replace(day=1)

    # --- APLICAR O FILTRO NAS BUSCAS ---
    # A gente só vai buscar registros cuja data seja MAIOR OU IGUAL (gte) a nossa start_date
    
    # KPIs
    solicitacoes_finalizadas = Solicitacao.objects.filter(status='FINALIZADO', data_criacao__gte=start_date).count()
    solicitacoes_em_aberto = Solicitacao.objects.filter(status='EM_ABERTO', data_criacao__gte=start_date).count()
    
    # Para os KPIs que não dependem de data, a gente mantém a busca completa
    total_arvores = InstanciaArvore.objects.count()
    diversidade_especies = Especie.objects.count()

    # Gráfico de Saúde (não costuma ser filtrado por data, mas se quisesse, seria InstanciaArvore.objects.filter(data_plantio__gte=start_date)...)
    dados_saude_query = InstanciaArvore.objects.values('estado_saude').annotate(total=Count('estado_saude')).order_by('estado_saude')
    mapa_saude = dict(InstanciaArvore.ESTADO_SAUDE_CHOICES)
    labels_saude = [mapa_saude.get(item['estado_saude'], 'N/A') for item in dados_saude_query]
    valores_saude = [item['total'] for item in dados_saude_query]

    # Gráfico Top 10 Espécies (baseado em árvores plantadas no período)
    top_especies_query = InstanciaArvore.objects.filter(data_plantio__gte=start_date) \
        .values('especie__nome_popular') \
        .annotate(total=Count('id')) \
        .order_by('-total')[:10]
    labels_top_especies = [item['especie__nome_popular'] for item in top_especies_query]
    valores_top_especies = [item['total'] for item in top_especies_query]
    
    # Gráfico de Plantios ao Longo do Tempo (já é filtrado por natureza, mas podemos refinar)
    plantios_por_mes = InstanciaArvore.objects.filter(data_plantio__gte=start_date) \
        .annotate(mes_plantio=TruncMonth('data_plantio')) \
        .values('mes_plantio') \
        .annotate(total=Count('id')) \
        .order_by('mes_plantio')
    labels_plantio = [p['mes_plantio'].strftime('%b/%Y') for p in plantios_por_mes]
    valores_plantio = [p['total'] for p in plantios_por_mes]

    context = {
        'pagina': 'relatorios',
        'periodo_selecionado': periodo_selecionado, # <<< Manda o filtro ativo pro template!
        
        # KPIs
        'total_arvores': total_arvores,
        'diversidade_especies': diversidade_especies,
        'solicitacoes_finalizadas': solicitacoes_finalizadas,
        'solicitacoes_em_aberto': solicitacoes_em_aberto,
        
        # Dados dos Gráficos
        'labels_saude': json.dumps(labels_saude),
        'valores_saude': json.dumps(valores_saude),
        'labels_top_especies': json.dumps(labels_top_especies),
        'valores_top_especies': json.dumps(valores_top_especies),
        'labels_plantio': json.dumps(labels_plantio),
        'valores_plantio': json.dumps(valores_plantio),
    }
    
    return render(request, 'core/relatorios.html', context)

@login_required
@require_http_methods(["DELETE"]) # Só aceita o método DELETE
def instancia_arvore_delete_api(request, pk):
    try:
        # Busca a árvore no banco de dados. Se não achar, dá erro 404.
        arvore = get_object_or_404(InstanciaArvore, pk=pk)
        
        # O comando pra apagar
        arvore.delete()
        
        # Manda a resposta de sucesso
        return JsonResponse({'status': 'ok', 'message': f'Árvore #{pk} foi deletada com sucesso!'})

    except Exception as e:
        # Se der qualquer outro erro, manda uma mensagem de falha
        return JsonResponse({'status': 'erro', 'message': str(e)}, status=500)

@login_required
def api_cidades_permitidas(request):
    """
    API que retorna a lista de cidades permitidas para o usuário logado.
    A cidade principal sempre virá primeiro na lista.
    """
    try:
        # Pega o perfil do maluco que tá logado
        profile = request.user.profile
        
        # Cria uma lista vazia pra gente colocar os nomes das cidades
        lista_cidades = []

        # 1. Primeiro, a cidade principal, que é a mais importante
        if profile.cidade_principal:
            lista_cidades.append(profile.cidade_principal.nome)

        # 2. Agora, pega as cidades secundárias
        # O .all() pega todos os objetos CidadePermitida que estão ligados a esse perfil
        cidades_secundarias = profile.cidades_secundarias.all()

        for cidade in cidades_secundarias:
            # Adiciona na lista só se o nome ainda não estiver lá (evita duplicar)
            if cidade.nome not in lista_cidades:
                lista_cidades.append(cidade.nome)
        
        # Devolve o "recibo" (JSON) com a lista de cidades que a gente montou
        return JsonResponse({'cidades': lista_cidades})

    except Profile.DoesNotExist:
        # Se por algum motivo o usuário não tiver um perfil, devolve uma lista vazia
        return JsonResponse({'cidades': []})
    except Exception as e:
        # Se der qualquer outro B.O., informa o erro
        return JsonResponse({'status': 'erro', 'message': str(e)}, status=500)
    
@login_required
def api_cidades_geo(request):
    profile = request.user.profile
    cidades = []

    # Cidade principal
    if profile.cidade_principal and profile.cidade_principal.geom:
        cidades.append({
            "nome": profile.cidade_principal.nome,
            "geom": profile.cidade_principal.geom
        })

    # Cidades secundárias
    for c in profile.cidades_secundarias.all():
        if c.geom and not any(ci['nome'] == c.nome for ci in cidades):
            cidades.append({
                "nome": c.nome,
                "geom": c.geom
            })

    return JsonResponse({"cidades": cidades})
