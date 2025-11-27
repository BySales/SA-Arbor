import json
from datetime import date, timedelta, datetime
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
# IMPORTS ADICIONADOS AQUI
from django.urls import reverse
from django.db.models import  OuterRef, Subquery
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_POST
# FIM DOS IMPORTS ADICIONADOS
from django.views.decorators.http import require_http_methods
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import Solicitacao, Projeto, Area, User, Equipe, Especie, InstanciaArvore, ImagemSolicitacao,TagCategory, Tag, CidadePermitida
from .forms import SolicitacaoForm, AreaForm, UserUpdateForm, ProfileUpdateForm, EquipeForm, EspecieForm, CadastroCidadaoForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.db.models.functions import TruncMonth
from .models import Profile, Notificacao
from django.db.models import Avg, F, ExpressionWrapper, DurationField


# --- VIEWS DE SOLICITAÇÃO ---

@login_required
def solicitacao_list(request):
    periodo = request.GET.get('periodo', 'total')
    status = request.GET.get('status')
    ordenar = request.GET.get('ordenar')
    cidade_id = request.GET.get('cidade')

    # --- 1. Busca Base Otimizada ---
    solicitacoes_base = Solicitacao.objects.select_related('cidade', 'cidadao').all()

    if status:
        solicitacoes_base = solicitacoes_base.filter(status=status)

    if cidade_id:
        solicitacoes_base = solicitacoes_base.filter(cidade__id=cidade_id)

    # --- 2. Filtros de Data (Dashboard) ---
    dashboard_qs = Solicitacao.objects.all()
    # (Mantive sua lógica de dashboard intocada aqui para os cards de cima)
    if periodo == 'hoje':
        dashboard_qs = dashboard_qs.filter(data_criacao__date=date.today())
    elif periodo == 'semana':
        uma_semana_atras = date.today() - timedelta(days=7)
        dashboard_qs = dashboard_qs.filter(data_criacao__date__gte=uma_semana_atras)
    elif periodo == 'mes':
        um_mes_atras = date.today() - timedelta(days=30)
        dashboard_qs = dashboard_qs.filter(data_criacao__date__gte=um_mes_atras)

    # --- 3. Filtros de Data (Lista Principal) ---
    solicitacoes_filtradas = solicitacoes_base
    if periodo == 'hoje':
        solicitacoes_filtradas = solicitacoes_base.filter(data_criacao__date=date.today())
    elif periodo == 'semana':
        uma_semana_atras = date.today() - timedelta(days=7)
        solicitacoes_filtradas = solicitacoes_base.filter(data_criacao__date__gte=uma_semana_atras)
    elif periodo == 'mes':
        um_mes_atras = date.today() - timedelta(days=30)
        solicitacoes_filtradas = solicitacoes_base.filter(data_criacao__date__gte=um_mes_atras)

    # =================================================================
    # 🔥 AQUI ESTÁ A MÁGICA DO TOGGLE (COMUNIDADE VS PESSOAL) 🔥
    # =================================================================
    if request.user.is_superuser or request.user.is_staff:
        # Se é chefe, vê tudo sempre.
        solicitacoes_query = solicitacoes_filtradas
    else:
        # Se é usuário comum, verifica a preferência no Perfil
        ver_tudo = False
        # Verifica se o perfil existe e se a opção está marcada
        if hasattr(request.user, 'profile') and request.user.profile.ver_todas_solicitacoes:
            ver_tudo = True
        
        if ver_tudo:
            # Modo Fofoca: Vê tudo (O template vai esconder os nomes)
            solicitacoes_query = solicitacoes_filtradas
        else:
            # Modo Privado: Vê só as dele (Padrão)
            solicitacoes_query = solicitacoes_filtradas.filter(cidadao=request.user)
    # =================================================================

    # --- 4. Ordenação ---
    if ordenar == 'data_asc':
        solicitacoes_ordenadas = solicitacoes_query.order_by('data_criacao')
    elif ordenar == 'tipo':
        solicitacoes_ordenadas = solicitacoes_query.order_by('tipo')
    else:
        solicitacoes_ordenadas = solicitacoes_query.order_by('-data_criacao')

    # --- 5. Paginação ---
    paginator = Paginator(solicitacoes_ordenadas, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # --- 6. Cálculos do Dashboard (Estatísticas) ---
    # Nota: Esses counts continuam globais para o Admin, 
    # mas você pode querer filtrar para o usuário comum se quiser que os cards mostrem só os dados dele.
    # Por enquanto, mantive a lógica original que conta do 'dashboard_qs' (Global).
    
    abertas_count = dashboard_qs.filter(status='EM_ABERTO').count()
    andamento_count = dashboard_qs.filter(status='EM_ANDAMENTO').count()
    finalizadas_count = dashboard_qs.filter(status='FINALIZADO').count()
    recusadas_count = dashboard_qs.filter(status='RECUSADO').count()
    denuncias_count = dashboard_qs.filter(tipo='DENUNCIA').count()
    sugestoes_count = dashboard_qs.filter(tipo='SUGESTAO').count()
    
    # Dados para Gráficos
    ultimos_7_dias = [date.today() - timedelta(days=i) for i in range(6, -1, -1)]
    solicitacoes_por_dia = (Solicitacao.objects.filter(data_criacao__date__in=ultimos_7_dias).annotate(dia=TruncDate('data_criacao')).values('dia').annotate(total=Count('id')).order_by('dia'))
    dados_recente = {dia_obj['dia']: dia_obj['total'] for dia_obj in solicitacoes_por_dia}
    datas_recente_labels = [dia.strftime('%d/%m') for dia in ultimos_7_dias]
    contagem_recente_data = [dados_recente.get(dia, 0) for dia in ultimos_7_dias]
    
    solicitacoes_em_andamento = Solicitacao.objects.filter(status='EM_ANDAMENTO')
    equipes_data = (solicitacoes_em_andamento.exclude(equipe_delegada__isnull=True).values('equipe_delegada__nome').annotate(total=Count('id')).order_by('-total'))
    equipes_labels = [item['equipe_delegada__nome'] for item in equipes_data]
    equipes_contagem = [item['total'] for item in equipes_data]

    # --- 7. Cidades para Filtro ---
    profile = request.user.profile
    cidades_ids = []
    if profile.cidade_principal:
        cidades_ids.append(profile.cidade_principal.id)
    cidades_ids.extend(profile.cidades_secundarias.all().values_list('id', flat=True))
    cidades_para_filtro = CidadePermitida.objects.filter(id__in=set(cidades_ids)).order_by('nome')

    # --- 8. Contexto Final ---
    # Se for usuário comum, vamos recalcular os cards para mostrar SÓ OS DELE
    # (Opcional: Se quiser que os cards de cima mostrem números globais, pode apagar esse bloco if/else abaixo)
    if not request.user.is_staff and not request.user.is_superuser:
        # Filtra os contadores para mostrar apenas o contexto do usuário
        meus_cards_qs = dashboard_qs.filter(cidadao=request.user)
        # Atualiza as variáveis que vão para os cards coloridos
        abertas_count = meus_cards_qs.filter(status='EM_ABERTO').count()
        andamento_count = meus_cards_qs.filter(status='EM_ANDAMENTO').count()
        finalizadas_count = meus_cards_qs.filter(status='FINALIZADO').count()
        recusadas_count = meus_cards_qs.filter(status='RECUSADO').count()

    context = {
        'solicitacoes': page_obj,
        'abertas_count': abertas_count,
        'andamento_count': andamento_count,
        'finalizadas_count': finalizadas_count,
        'recusadas_count': recusadas_count,
        'periodo_selecionado': periodo,
        'status_selecionado': status,
        'ordenar_selecionado': ordenar,
        'cidades_para_filtro': cidades_para_filtro,
        'cidade_selecionada': cidade_id,
        'denuncias_count': denuncias_count,
        'sugestoes_count': sugestoes_count,
        'datas_recente_labels': json.dumps(datas_recente_labels),
        'contagem_recente_data': json.dumps(contagem_recente_data),
        'equipes_labels': json.dumps(equipes_labels),
        'equipes_contagem': json.dumps(equipes_contagem),
        
        # Variáveis extras para o dashboard pessoal (home) se precisar
        'minhas_solicitacoes_abertas': abertas_count,
        'minhas_solicitacoes_andamento': andamento_count,
        'minhas_solicitacoes_finalizadas': finalizadas_count,
    }
    return render(request, 'core/solicitacao_list.html', context)

@login_required
def solicitacao_create(request):
    if request.method == 'POST':
        
        # ======================================================
        # 🔥 MODIFICAÇÃO 1: O "CHEFE MALANDRO" (POST)
        # Adiciona o status 'EM_ABERTO' pro usuário comum
        # ======================================================
        
        # 1. Copia os dados do POST pra poder mexer neles
        post_data = request.POST.copy()

        # 2. Se o usuário NÃO for staff E o campo 'status' não veio no envelope...
        if not request.user.is_staff and 'status' not in post_data:
            # 3. ...a gente bota o 'status' default NA MÃO.
            post_data['status'] = 'EM_ABERTO'
        
        # ======================================================
        # FIM DA MODIFICAÇÃO 1
        # ======================================================

        # 4. Agora a gente cria o form com os dados já "corrigidos"
        #    (Troca 'request.POST' por 'post_data')
        form = SolicitacaoForm(post_data, request.FILES, user=request.user)
        
        # O resto da tua lógica de POST continua igual...
        if len(request.FILES.getlist('imagens')) > 10:
            return JsonResponse({'success': False, 'errors': {'imagens': ['Você só pode enviar no máximo 10 imagens.']}}, status=400)

        if form.is_valid():
            solicitacao = form.save(commit=False)
            solicitacao.cidadao = request.user
            solicitacao.save()
            
            imagens = request.FILES.getlist('imagens')
            for imagem_file in imagens:
                ImagemSolicitacao.objects.create(solicitacao=solicitacao, imagem=imagem_file)
            
            messages.success(request, 'Solicitação criada com sucesso!')
            return JsonResponse({'success': True, 'redirect_url': reverse('solicitacao_list')})
        else:
            # É aqui que o erro ("campo obrigatório") era gerado. Agora não vai mais.
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    else: # GET
        # ======================================================
        # 🔥 MODIFICAÇÃO 2: O "LEÃO DE CHÁCARA" (GET)
        # Barra o usuário que não tem cidade no perfil
        # ======================================================
        try:
            profile = request.user.profile
            
            # Checa se o maluco tem PELO MENOS UMA cidade (principal ou secundária)
            tem_cidade_principal = profile.cidade_principal is not None
            tem_cidades_secundarias = profile.cidades_secundarias.exists()

            if not tem_cidade_principal and not tem_cidades_secundarias:
                # Se não tem... CHUTA ELE!
                messages.error(request, "Você precisa definir sua 'Cidade Principal' em 'Configurações' antes de poder criar uma solicitação.")
                return redirect('configuracoes')
                
        except Profile.DoesNotExist:
             # Se o cara nem perfil tem (B.O. grave), chuta ele também
             messages.error(request, "Seu perfil de usuário não foi encontrado. Contate o administrador.")
             return redirect('home')
        
        # ======================================================
        # FIM DA MODIFICAÇÃO 2
        # ======================================================
        
        # Se ele passou pelo Leão de Chácara, aí sim ele vê o form
        form = SolicitacaoForm(user=request.user)
        
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
    # 1. O CHEFE BUSCA A COMANDA (SOLICITAÇÃO) NO ESTOQUE
    solicitacao = get_object_or_404(Solicitacao, pk=pk)
    
    # 2. O LEÃO DE CHÁCARA (BOUNCER)
    # Se o cara não é staff E não é o dono da comanda...
    if not request.user.is_staff and solicitacao.cidadao != request.user:
        messages.error(request, f"Tu não pode mexer na solicitação #{pk}, ela não é tua, parça.")
        return redirect('solicitacao_list')

    # 3. CHEFE VÊ SE O PEDIDO É PRA ATUALIZAR (POST)
    if request.method == 'POST':
        
        # ======================================================
        # 🔥 ANTES DE OUVIR A MUDANÇA, ELE ANOTA O ESTADO ANTIGO
        # ======================================================
        status_antigo = solicitacao.get_status_display() 
        equipe_antiga = solicitacao.equipe_delegada
        
        # 4. O CHEFE PEGA O PAPEL DE ATUALIZAÇÃO (O FORM)
        form = SolicitacaoForm(request.POST, request.FILES, instance=solicitacao, user=request.user)

        # 5. OUTRO LEÃO DE CHÁCARA (BOUNCER DAS FOTOS)
        imagens_novas = request.FILES.getlist('imagens')
        imagens_atuais_count = solicitacao.imagens.count()
        if (imagens_atuais_count + len(imagens_novas)) > 10:
            error_msg = f'Não pode ter mais de 10 imagens. Esta solicitação já tem {imagens_atuais_count}.'
            return JsonResponse({'success': False, 'errors': {'imagens': [error_msg]}}, status=400)

        # 6. O CHEFE CONFERE SE O PEDIDO TÁ PREENCHIDO CERTO
        if form.is_valid():
            
            # 7. PEGA A COMANDA ATUALIZADA, MAS SEGURA ANTES DE SALVAR
            solicitacao_instance = form.save(commit=False)
            
            # ======================================================
            # 🔥 LÓGICA DO "MENSAGEIRO" (O X9 DAS NOTIFICAÇÕES)
            # ======================================================
            
            # 7a. O Mensageiro monta a lista de quem quer saber da fofoca
            destinatarios = set()
            if solicitacao.cidadao: # O dono
                destinatarios.add(solicitacao.cidadao)
            for interessado in solicitacao.interessados.all(): # A galera do "sininho"
                destinatarios.add(interessado)

            # 7b. O Mensageiro vê se o STATUS mudou
            if 'status' in form.changed_data:
                status_novo = solicitacao_instance.get_status_display() # Pega o valor novo
                mensagem = f"A Solicitação #{solicitacao.id} mudou de status: de '{status_antigo}' para '{status_novo}'."
                
                # Manda o papo pra toda a lista
                for user in destinatarios:
                    Notificacao.objects.create(
                        usuario=user,
                        solicitacao=solicitacao_instance,
                        mensagem=mensagem
                    )

            # 7c. O Mensageiro vê se a EQUIPE mudou
            if 'equipe_delegada' in form.changed_data:
                equipe_nova = solicitacao_instance.equipe_delegada
                mensagem = ""
                if equipe_nova and equipe_antiga: # Se trocou de uma pra outra
                    mensagem = f"A Solicitação #{solicitacao.id} foi transferida da equipe '{equipe_antiga.nome}' para '{equipe_nova.nome}'."
                elif equipe_nova: # Se foi delegada (antes era Nulo)
                    mensagem = f"A Solicitação #{solicitacao.id} foi delegada para a equipe '{equipe_nova.nome}'."
                else: # Se foi "des-delegada" (ficou Nulo)
                    mensagem = f"A Solicitação #{solicitacao.id} foi removida da equipe '{equipe_antiga.nome}'."
                
                for user in destinatarios:
                    Notificacao.objects.create(
                        usuario=user,
                        solicitacao=solicitacao_instance,
                        mensagem=mensagem
                    )

            # 7d. O Mensageiro vê se foi RECUSADA (e tem motivo)
            if 'motivo_recusa' in form.changed_data and solicitacao_instance.status == 'RECUSADO':
                motivo_curto = solicitacao_instance.motivo_recusa[:70] + '...' if len(solicitacao_instance.motivo_recusa) > 70 else solicitacao_instance.motivo_recusa
                mensagem = f"A Solicitação #{solicitacao.id} foi recusada. Motivo: '{motivo_curto}'"
                
                for user in destinatarios:
                    Notificacao.objects.create(
                        usuario=user,
                        solicitacao=solicitacao_instance,
                        mensagem=mensagem
                    )
            # ======================================================
            # FIM DO MENSAGEIRO
            # ======================================================

            # ======================================================
            # 8. LÓGICA DO CARIMBO AUTOMÁTICO (TUA LÓGICA ANTIGA)
            # ======================================================
            if 'status' in form.changed_data and (solicitacao_instance.status == 'FINALIZADO' or solicitacao_instance.status == 'RECUSADO'):
                solicitacao_instance.data_finalizacao = timezone.now()
            
            # ======================================================
            # 9. LÓGICA DE CRIAÇÃO DA ÁRVORE (TUA LÓGICA ANTIGA)
            # ======================================================
            especie_para_plantar = form.cleaned_data.get('especie_plantada')
            if solicitacao_instance.status == 'FINALIZADO' and especie_para_plantar:
                InstanciaArvore.objects.create(
                    especie=especie_para_plantar,
                    latitude=solicitacao_instance.latitude,
                    longitude=solicitacao_instance.longitude,
                    estado_saude='BOA',
                    data_plantio=timezone.now().date()
                )

            # 10. AGORA SIM! O CHEFE SALVA A COMANDA NO ESTOQUE
            solicitacao_instance.save()
            
            # 11. O CHEFE SALVA AS FOTOS NOVAS
            for imagem_file in imagens_novas:
                ImagemSolicitacao.objects.create(solicitacao=solicitacao, imagem=imagem_file)
            
            # 12. O CHEFE AVISA QUE DEU TUDO CERTO (JSON pro JS)
            messages.success(request, f'Solicitação #{solicitacao.id} foi atualizada com sucesso!')
            return JsonResponse({'success': True, 'redirect_url': reverse('solicitacao_list')})
        
        else: # Se o formulário for inválido
            # 13. O CHEFE AVISA QUE O PEDIDO VEIO ZOADO (JSON pro JS)
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            
    else: # 14. SE O PEDIDO FOR SÓ PRA VER (GET)
        # O Chefe só monta o prato (HTML) com o formulário preenchido
        form = SolicitacaoForm(instance=solicitacao, user=request.user)
    
    context = {
        'form': form,
        'solicitacao': solicitacao 
    }
    return render(request, 'core/solicitacao_form.html', context)

@login_required
def solicitacao_delete(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)
    if not request.user.is_staff and solicitacao.cidadao != request.user:
        # ...CHUTA ELE! Manda uma mensagem e joga de volta pra lista.
        messages.error(request, f"Você não pode apagar a solicitação #{pk}, ela não é sua.")
        return redirect('solicitacao_list')
    if request.method == 'POST':
        id_solicitacao = solicitacao.id
        solicitacao.delete()
        messages.success(request, f'Solicitação #{id_solicitacao} foi deletada com sucesso!')
        return redirect('solicitacao_list')
    return render(request, 'core/solicitacao_confirm_delete.html', {'object': solicitacao})


# --- VIEWS DE EQUIPE ---

@login_required
@user_passes_test(lambda u: u.is_staff, login_url='home')
def equipe_list(request):
    """
    View 2.0 do painel de equipes, com busca otimizada.
    """
    trinta_dias_atras = timezone.now() - timedelta(days=30)
    
    # Esta é a SUBQUERY que vai contar as tarefas concluídas nos últimos 30 dias para cada equipe
    tarefas_concluidas_recentemente = Solicitacao.objects.filter(
        equipe_delegada=OuterRef('pk'),
        status='FINALIZADO',
        data_finalizacao__gte=trinta_dias_atras
    ).values('equipe_delegada').annotate(count=Count('pk')).values('count')

    # A MÁGICA ACONTECE AQUI: uma única viagem ao banco de dados!
    equipes_com_stats = Equipe.objects.annotate(
        # Conta tarefas ativas
        tarefas_ativas=Count('solicitacao', filter=Q(solicitacao__status='EM_ANDAMENTO')),
        # Usa a subquery para contar as concluídas
        tarefas_concluidas=Subquery(tarefas_concluidas_recentemente),
        # Conta denúncias e sugestões
        denuncias_count=Count('solicitacao', filter=Q(solicitacao__tipo='DENUNCIA')),
        sugestoes_count=Count('solicitacao', filter=Q(solicitacao__tipo='SUGESTAO')),
    ).prefetch_related('membros__profile') # Já busca os membros e seus perfis de uma vez

    # Pega usuários que são staff mas não estão em nenhuma equipe
    agentes_livres = User.objects.filter(is_staff=True, equipes__isnull=True).select_related('profile')

    context = {
        'equipes_com_stats': equipes_com_stats,
        'agentes_livres': agentes_livres,
    }
    return render(request, 'core/equipe_list.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='home') # <--- 🔥 O LEÃO DE CHÁCARA V.I.P.
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
@user_passes_test(lambda u: u.is_staff, login_url='home')
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
    
    # --- 🔥 NOVIDADE: BUSCAR DADOS EXTRAS PARA O PAINEL LATERAL ---
    
    # 1. Pega a tarefa que tá rolando AGORA (Status Em Andamento)
    tarefa_atual = Solicitacao.objects.filter(
        equipe_delegada=equipe, 
        status='EM_ANDAMENTO'
    ).order_by('-data_criacao').first() # Pega a mais recente
    
    # 2. Pega as últimas 3 que eles resolveram (Status Finalizado)
    historico_tarefas = Solicitacao.objects.filter(
        equipe_delegada=equipe, 
        status='FINALIZADO'
    ).order_by('-data_finalizacao')[:3]

    context = {
        'form': form, 
        'titulo': f'Editar Equipe: {equipe.nome}',
        # Manda as novidades pro template
        'tarefa_atual': tarefa_atual,
        'historico_tarefas': historico_tarefas,
        'equipe': equipe
    }
    return render(request, 'core/equipe_form.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff, login_url='home')
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
@user_passes_test(lambda u: u.is_staff, login_url='home')
def especie_list(request):
    # 1. Pega TODAS as tags que vieram na URL (agora é uma lista)
    tags_filtro = request.GET.getlist('tag')
    
    # 2. Começa a busca base
    especies = Especie.objects.prefetch_related('tags').order_by('nome_popular')
    
    # 3. Filtro Acumulativo (AND)
    tags_ativas = []
    if tags_filtro:
        # Para cada tag na URL, a gente filtra mais um pouco
        for tag_id in tags_filtro:
            especies = especies.filter(tags__id=tag_id)
        
        # Pega os objetos das tags ativas pra mostrar bonito na tela
        tags_ativas = Tag.objects.filter(id__in=tags_filtro)

    # 4. Pega todas as categorias e suas tags para o botão "Adicionar Filtro"
    # (O distinct é pra evitar duplicatas se a modelagem permitir)
    categorias_tags = TagCategory.objects.prefetch_related('tags').all().distinct()

    # 5. Paginação
    paginator = Paginator(especies, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'especies': page_obj,
        'tags_ativas': tags_ativas,    # Agora é uma lista de objetos
        'categorias_tags': categorias_tags, # Pro dropdown novo
        # Passamos os IDs atuais pra facilitar a vida do template
        'tags_ativas_ids': [int(t) for t in tags_filtro if t.isdigit()]
    }
    return render(request, 'core/especie_list.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff, login_url='home')
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
@user_passes_test(lambda u: u.is_staff, login_url='home')
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
@user_passes_test(lambda u: u.is_staff, login_url='home')
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

class AreaDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView): # <--- 🔥 MIXIN DO LEÃO DE CHÁCARA
    model = Area 
    template_name = 'core/area_confirm_delete.html'
    success_url = reverse_lazy('mapa') # Você já usa o reverse_lazy, perfeito

    # 🔥 A REGRA: "Só passa se for staff"
    def test_func(self):
        return self.request.user.is_staff

    # 🔥 Se não for staff, CHUTA PRA HOME
    def get_login_url(self):
        return reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Confirmar Deleção de Área'
        return context


# --- VIEW DO MAPA ---
@login_required
def mapa_view(request):
    solicitacao_foco_id = request.GET.get('solicitacao_id')
    area_foco_id = request.GET.get('area_id') # Mantido caso use para focar área
    
    # 1. Busca as ÁRVORES (como antes)
    instancias_de_arvores = InstanciaArvore.objects.select_related('especie').all()
    arvores_data = [{"id": instancia.id, "nome": instancia.especie.nome_popular, "nome_cientifico": instancia.especie.nome_cientifico, "descricao": instancia.especie.descricao, "lat": instancia.latitude, "lon": instancia.longitude, "saude": instancia.get_estado_saude_display(), "plantio": instancia.data_plantio.strftime('%d/%m/%Y') if instancia.data_plantio else 'N/A'} for instancia in instancias_de_arvores]
    
    # 2. Busca SÓ as SOLICITAÇÕES ATIVAS para o mapa principal (como antes)
    solicitacoes_com_coords = Solicitacao.objects.filter(
        latitude__isnull=False, 
        longitude__isnull=False,
        status__in=['EM_ABERTO', 'EM_ANDAMENTO'] 
    )
    solicitacoes_data = [{
    "id": solicitacao.id, 
    "tipo_display": solicitacao.get_tipo_display(), 
    "tipo_codigo": solicitacao.tipo, 
    "status": solicitacao.get_status_display(), 
    "descricao": solicitacao.descricao, 
    "lat": solicitacao.latitude, 
    "lon": solicitacao.longitude,
    # 🔥 ADICIONA ESSAS DUAS LINHAS AQUI:
    "cidadao_id": solicitacao.cidadao.id,
    "cidadao_nome": solicitacao.cidadao.username
} for solicitacao in solicitacoes_com_coords]
    
    # 3. Busca as ÁREAS (como antes)
    areas_salvas = Area.objects.filter(geom__isnull=False)
    areas_data = [{"id": area.id, "nome": area.nome, "geom": area.geom, "tipo": area.get_tipo_display(), "status": area.get_status_display()} for area in areas_salvas]
    
    # 4. Busca as ESPÉCIES para os modais (como antes)
    especies_catalogo = Especie.objects.all().order_by('nome_popular')
    opcoes_saude = InstanciaArvore.ESTADO_SAUDE_CHOICES 
    form_area = AreaForm() # Você usa isso? Se sim, mantido.

    # ======================================================
    # ============ LÓGICA DO "GPS FANTASMA" ============
    # ======================================================
    foco_solicitacao_data = None # Começa como nulo
    if solicitacao_foco_id:
        try:
            # Tenta buscar a solicitação específica pelo ID, NÃO IMPORTA O STATUS
            foco_solicitacao_obj = Solicitacao.objects.get(
                pk=solicitacao_foco_id,
                latitude__isnull=False, # Garante que ela tem coords
                longitude__isnull=False
            )
            # Formata os dados dela pra mandar pro JS
            foco_solicitacao_data = {
                "id": foco_solicitacao_obj.id,
                "tipo_display": foco_solicitacao_obj.get_tipo_display(),
                "tipo_codigo": foco_solicitacao_obj.tipo,
                "status": foco_solicitacao_obj.get_status_display(), # Mostra o status real (Finalizado/Recusado)
                "descricao": foco_solicitacao_obj.descricao,
                "lat": foco_solicitacao_obj.latitude,
                "lon": foco_solicitacao_obj.longitude
            }
        except ObjectDoesNotExist: # Se o ID for inválido, não faz nada
            pass 
    # ======================================================

    context = {
        'arvores_data': arvores_data,
        'solicitacoes_data': solicitacoes_data, # Só as ativas
        'areas_data': areas_data,
        'form_area': form_area,
        'especies_catalogo': especies_catalogo,
        'opcoes_saude': opcoes_saude,
        # 'solicitacao_foco_id': solicitacao_foco_id, # Não precisamos mais mandar o ID solto
        'area_foco_id': area_foco_id,
        'foco_solicitacao_data': foco_solicitacao_data # <<< MANDA OS DADOS DO "FANTASMA"
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
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        # form = UserCreationForm(request.POST) <--- TROCA ESSA LINHA
        form = CadastroCidadaoForm(request.POST) # <--- POR ESSA

        if form.is_valid():
            form.save() # A mágica do nosso save() novo acontece aqui
            return redirect('login')
    else:
        # form = UserCreationForm() <--- TROCA ESSA LINHA
        form = CadastroCidadaoForm() # <--- POR ESSA

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
@user_passes_test(lambda u: u.is_staff, login_url='home')
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
@user_passes_test(lambda u: u.is_staff, login_url='home')
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

@login_required
def search_results_view(request):
    query = request.GET.get('q')
    context = {'query': query}

    # Zera os contadores
    solicitacoes_results = Solicitacao.objects.none() # Começa com uma lista vazia
    especies_results = Especie.objects.none()
    equipes_results = Equipe.objects.none()


    if query:
        if request.user.is_staff:
            solicitacoes_results = Solicitacao.objects.filter(
                Q(descricao__icontains=query) | Q(cidadao__username__icontains=query)).distinct(
            )
            especies_results = Especie.objects.filter(
          		Q(nome_popular__icontains=query) | Q(nome_cientifico__icontains=query)
        	).distinct()

            equipes_results = Equipe.objects.filter(
                Q(nome__icontains=query)).distinct()
        else:
            solicitacoes_results + Solicitacao.objects.filter(
                cidadao=request.user
            ).filter(
                Q(descricao__icontains=query)).distinct(
            )
        

        context['solicitacoes_results'] = solicitacoes_results
        context['especies_results'] = especies_results
        context['equipes_results'] = equipes_results
        total_results = len(solicitacoes_results) + len(especies_results) + len(equipes_results)
        context['total_results'] = total_results


    return render(request, 'core/search_results.html', context)


# --- VIEW DE OBRAS (KANBAN) ---

@login_required
@user_passes_test(lambda u: u.is_staff, login_url='home')
def planejamentos_view(request):
    """
    View da nova Sala de Estratégia, agora com KPIs de performance.
    """
    hoje = timezone.now()

    # --- MÓDULO 1: Balanço das Tropas ---
    dados_carga_equipes = Equipe.objects.filter(solicitacao__status='EM_ANDAMENTO').annotate(
        tarefas_ativas=Count('solicitacao')
    ).values('nome', 'tarefas_ativas').order_by('-tarefas_ativas')
    labels_equipes = [item['nome'] for item in dados_carga_equipes]
    data_equipes = [item['tarefas_ativas'] for item in dados_carga_equipes]
    agentes_livres = User.objects.filter(is_staff=True, equipes__isnull=True).order_by('username')
    
    # --- MÓDULO 2: Arsenal Biológico ---
    top_especies = InstanciaArvore.objects.values('especie__nome_popular').annotate(total=Count('id')).order_by('-total')[:10]
    labels_top_especies = [item['especie__nome_popular'] for item in top_especies]
    data_top_especies = [item['total'] for item in top_especies]
    especies_plantadas_ids = set(InstanciaArvore.objects.values_list('especie_id', flat=True).distinct())
    especies_nao_utilizadas = Especie.objects.exclude(id__in=especies_plantadas_ids).order_by('nome_popular')

    # ======================================================
    # MÓDULO NOVO: O Placar do Jogo (KPIs)
    # ======================================================
    # --- KPI 1: Termômetro de Plantio ---
    plantios_mes_atual = InstanciaArvore.objects.filter(
        data_plantio__year=hoje.year,
        data_plantio__month=hoje.month
    ).count()

    # --- KPI 2: Fila de Atendimento ---
    resolvidas_mes_atual = Solicitacao.objects.filter(
        data_finalizacao__year=hoje.year,
        data_finalizacao__month=hoje.month
    ).count()

    # --- KPI 3: Velocímetro da Equipe ---
    trinta_dias_atras = hoje - timedelta(days=30)
    solicitacoes_recentes = Solicitacao.objects.filter(
        status='FINALIZADO',
        data_finalizacao__gte=trinta_dias_atras
    )
    
    # Calcula a média da diferença entre a data de finalização e a de criação
    tempo_medio_timedelta = solicitacoes_recentes.aggregate(
        tempo_medio=Avg(F('data_finalizacao') - F('data_criacao'))
    )['tempo_medio']
    
    tempo_medio_str = "N/A"
    if tempo_medio_timedelta:
        dias = tempo_medio_timedelta.days
        horas = tempo_medio_timedelta.seconds // 3600
        tempo_medio_str = f"{dias}d {horas}h"

    context = {
        'pagina': 'planejamentos',
        
        # Dados Módulo Balanço das Tropas
        'labels_equipes_carga': json.dumps(labels_equipes),
        'data_equipes_carga': json.dumps(data_equipes),
        'agentes_livres': agentes_livres,
        
        # Dados Módulo Arsenal Biológico
        'labels_top_especies': json.dumps(labels_top_especies),
        'data_top_especies': json.dumps(data_top_especies),
        'especies_nao_utilizadas': especies_nao_utilizadas,

        # ======================================================
        # Dados do novo "Placar do Jogo"
        'plantios_mes_atual': plantios_mes_atual,
        'resolvidas_mes_atual': resolvidas_mes_atual,
        'tempo_medio_str': tempo_medio_str,
        # ======================================================
    }
    
    return render(request, 'core/planejamentos.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff, login_url='home')
def api_heatmap_denuncias(request):
    """
    Retorna uma lista de coordenadas [lat, lon] para todas as solicitações
    do tipo 'DENUNCIA' que pertencem às cidades do usuário.
    """
    # Pega as cidades permitidas para o usuário logado
    profile = request.user.profile
    cidades_ids = []
    if profile.cidade_principal:
        cidades_ids.append(profile.cidade_principal.id)
    cidades_ids.extend(profile.cidades_secundarias.all().values_list('id', flat=True))

    # Filtra as denúncias que têm coordenadas e pertencem a essas cidades
    denuncias = Solicitacao.objects.filter(
        tipo='DENUNCIA',
        latitude__isnull=False,
        longitude__isnull=False,
        cidade__id__in=set(cidades_ids)
    ).values_list('latitude', 'longitude')

    # Converte o resultado para uma lista e retorna como JSON
    coordenadas = list(denuncias)
    return JsonResponse(coordenadas, safe=False)

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
@user_passes_test(lambda u: u.is_staff, login_url='home')
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
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'core/recuperar_senha.html')

# Adicione esta nova view
@login_required
def home_view(request):

    context = {} # Começa o contexto vazio
    
    # Se o maluco for da DIRETORIA (staff)...
    if request.user.is_staff:
        # --- Ele vê o DASHBOARD V.I.P. (O teu código original) ---
        instancias_count = InstanciaArvore.objects.count()
        solicitacoes_abertas_count = Solicitacao.objects.filter(status='EM_ABERTO').count()
        equipes_count = Equipe.objects.count()
        especies_count = Especie.objects.count()
        # Pega as 5 últimas do SISTEMA INTEIRO
        ultimas_solicitacoes = Solicitacao.objects.order_by('-data_criacao')[:5]

        context = {
            'instancias_count': instancias_count,
            'solicitacoes_abertas_count': solicitacoes_abertas_count,
            'equipes_count': equipes_count,
            'especies_count': especies_count,
            'ultimas_solicitacoes': ultimas_solicitacoes,
            'is_staff_dashboard': True # <--- Uma "bandeira" pro HTML saber
        }

    # Se for do POVÃO (usuário comum)...
    else:
        # --- Ele vê o DASHBOARD PESSOAL (focado nele) ---
        
        # Total de árvores da cidade (isso é público, beleza)
        instancias_count = InstanciaArvore.objects.count() 
        
        # Contagem de solicitações SÓ DELE
        minhas_solicitacoes_abertas = Solicitacao.objects.filter(
            cidadao=request.user, 
            status='EM_ABERTO'
        ).count()
        
        # Contagem de solicitações SÓ DELE
        minhas_solicitacoes_andamento = Solicitacao.objects.filter(
            cidadao=request.user, 
            status='EM_ANDAMENTO'
        ).count()
        
        # Contagem de solicitações SÓ DELE
        minhas_solicitacoes_finalizadas = Solicitacao.objects.filter(
            cidadao=request.user, 
            status='FINALIZADO'
        ).count()
        
        # Pega as 5 últimas SÓ DELE
        ultimas_solicitacoes = Solicitacao.objects.filter(
            cidadao=request.user
        ).order_by('-data_criacao')[:5]

        context = {
            'instancias_count': instancias_count,
            'minhas_solicitacoes_abertas': minhas_solicitacoes_abertas,
            'minhas_solicitacoes_andamento': minhas_solicitacoes_andamento,
            'minhas_solicitacoes_finalizadas': minhas_solicitacoes_finalizadas,
            'ultimas_solicitacoes': ultimas_solicitacoes,
            'is_staff_dashboard': False # <--- A "bandeira" pro HTML
        }

    # ======================================================
    # O render é o mesmo, mas o 'context' agora é inteligente
    # ======================================================
    return render(request, 'core/home.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff, login_url='home')
def relatorios_view(request):
    """
    View para a Central de Relatórios com filtros de período e múltiplos gráficos.
    """
    periodo_selecionado = request.GET.get('periodo', 'mes')

    today = timezone.now().date()
    start_date = None

    if periodo_selecionado == 'semana':
        start_date = today - timedelta(days=7)
    elif periodo_selecionado == 'ano':
        start_date = today.replace(month=1, day=1)
    else: 
        start_date = today.replace(day=1)

    # --- KPIs ---
    solicitacoes_finalizadas = Solicitacao.objects.filter(status='FINALIZADO', data_criacao__gte=start_date).count()
    solicitacoes_em_aberto = Solicitacao.objects.filter(status='EM_ABERTO', data_criacao__gte=start_date).count()
    total_arvores = InstanciaArvore.objects.count()
    diversidade_especies = Especie.objects.count()

    # ======================================================
    # GRÁFICO 1: DISTRIBUIÇÃO (PIZZA/ROSCA)
    # ======================================================
    
    # A: Saúde das Árvores
    dados_saude_query = InstanciaArvore.objects.values('estado_saude').annotate(total=Count('estado_saude')).order_by('estado_saude')
    mapa_saude = dict(InstanciaArvore.ESTADO_SAUDE_CHOICES)
    labels_saude = [mapa_saude.get(item['estado_saude'], 'N/A') for item in dados_saude_query]
    valores_saude = [item['total'] for item in dados_saude_query]

    # B: Status das Solicitações
    dados_status_solic_query = Solicitacao.objects.filter(data_criacao__gte=start_date) \
        .values('status').annotate(total=Count('status')).order_by('status')
    mapa_status = dict(Solicitacao.STATUS_CHOICES)
    labels_status_solic = [mapa_status.get(item['status'], 'N/A') for item in dados_status_solic_query]
    valores_status_solic = [item['total'] for item in dados_status_solic_query]

    # C: Status das Áreas (NOVO 🔥) - Visão geral de planejamento
    dados_areas_query = Area.objects.values('status').annotate(total=Count('status')).order_by('-total')
    mapa_areas = dict(Area.STATUS_AREA_CHOICES)
    labels_areas = [mapa_areas.get(item['status'], item['status']) for item in dados_areas_query]
    valores_areas = [item['total'] for item in dados_areas_query]

    # ======================================================
    # GRÁFICO 2: RANKING E CATEGORIAS (BARRAS)
    # ======================================================

    # A: Top 10 Espécies
    top_especies_query = InstanciaArvore.objects.filter(data_plantio__gte=start_date) \
        .values('especie__nome_popular') \
        .annotate(total=Count('id')) \
        .order_by('-total')[:10]
    labels_top_especies = [item['especie__nome_popular'] for item in top_especies_query]
    valores_top_especies = [item['total'] for item in top_especies_query]

    # B: Solicitações por Tipo
    dados_tipo_query = Solicitacao.objects.filter(data_criacao__gte=start_date) \
        .values('tipo').annotate(total=Count('id'))
    mapa_tipo = dict(Solicitacao.TIPO_CHOICES)
    labels_tipo = [mapa_tipo.get(item['tipo'], item['tipo']) for item in dados_tipo_query]
    valores_tipo = [item['total'] for item in dados_tipo_query]

    # C: Produtividade das Equipes (NOVO 🔥) - Quem resolveu mais?
    equipes_query = Solicitacao.objects.filter(status='FINALIZADO', data_finalizacao__gte=start_date) \
        .exclude(equipe_delegada__isnull=True) \
        .values('equipe_delegada__nome') \
        .annotate(total=Count('id')) \
        .order_by('-total')
    labels_equipes = [item['equipe_delegada__nome'] for item in equipes_query]
    valores_equipes = [item['total'] for item in equipes_query]

    # ======================================================
    # GRÁFICO 3: LINHA DO TEMPO
    # ======================================================

    # A: Plantios
    plantios_por_mes = InstanciaArvore.objects.filter(data_plantio__gte=start_date) \
        .annotate(mes=TruncMonth('data_plantio')) \
        .values('mes').annotate(total=Count('id')).order_by('mes')
    labels_plantio = [p['mes'].strftime('%b/%Y') for p in plantios_por_mes]
    valores_plantio = [p['total'] for p in plantios_por_mes]

    # B: Resoluções
    resolucoes_por_mes = Solicitacao.objects.filter(status='FINALIZADO', data_finalizacao__gte=start_date) \
        .annotate(mes=TruncMonth('data_finalizacao')) \
        .values('mes').annotate(total=Count('id')).order_by('mes')
    labels_resolucao = [p['mes'].strftime('%b/%Y') for p in resolucoes_por_mes]
    valores_resolucao = [p['total'] for p in resolucoes_por_mes]

    context = {
        'pagina': 'relatorios',
        'periodo_selecionado': periodo_selecionado,
        
        'total_arvores': total_arvores,
        'diversidade_especies': diversidade_especies,
        'solicitacoes_finalizadas': solicitacoes_finalizadas,
        'solicitacoes_em_aberto': solicitacoes_em_aberto,
        
        # Gráfico 1
        'labels_saude': json.dumps(labels_saude),
        'valores_saude': json.dumps(valores_saude),
        'labels_status_solic': json.dumps(labels_status_solic),
        'valores_status_solic': json.dumps(valores_status_solic),
        'labels_areas': json.dumps(labels_areas),       # NOVO
        'valores_areas': json.dumps(valores_areas),     # NOVO
        
        # Gráfico 2
        'labels_top_especies': json.dumps(labels_top_especies),
        'valores_top_especies': json.dumps(valores_top_especies),
        'labels_tipo': json.dumps(labels_tipo),
        'valores_tipo': json.dumps(valores_tipo),
        'labels_equipes': json.dumps(labels_equipes),   # NOVO
        'valores_equipes': json.dumps(valores_equipes), # NOVO
        
        # Gráfico 3
        'labels_plantio': json.dumps(labels_plantio),
        'valores_plantio': json.dumps(valores_plantio),
        'labels_resolucao': json.dumps(labels_resolucao),
        'valores_resolucao': json.dumps(valores_resolucao),
    }
    
    return render(request, 'core/relatorios.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff, login_url='home')
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

@login_required
@require_POST # Só aceita POST
@csrf_exempt # A gente vai chamar com JS, facilita
def toggle_interesse_api(request, pk):
    try:
        solicitacao = get_object_or_404(Solicitacao, pk=pk)
        user = request.user
        
        if user in solicitacao.interessados.all():
            # Se já segue, para de seguir
            solicitacao.interessados.remove(user)
            interessado = False
        else:
            # Se não segue, começa a seguir
            solicitacao.interessados.add(user)
            interessado = True
            
        return JsonResponse({'status': 'ok', 'interessado': interessado, 'count': solicitacao.interessados.count()})
    except Exception as e:
        return JsonResponse({'status': 'erro', 'message': str(e)}, status=500)

@login_required
@require_POST  # Só aceita POST
@csrf_exempt   # Facilita a vida pro nosso JS
def api_marcar_notificacoes_lidas(request):
    """
    API "Deduradora": Pega todas as notificações NÃO LIDAS
    do usuário logado e marca elas como LIDAS.
    """
    try:
        # 1. Acha todas as notificações do usuário com 'lida=False'
        notificacoes_para_limpar = Notificacao.objects.filter(
            usuario=request.user, 
            lida=False
        )
        
        # 2. Manda o "update" de uma vez só (muito rápido)
        notificacoes_para_limpar.update(lida=True)
        
        # 3. Manda o "jóia" de volta pro JS
        return JsonResponse({'status': 'ok'})
    
    except Exception as e:
        return JsonResponse({'status': 'erro', 'message': str(e)}, status=500)


def sobre_view(request):
    return render(request, 'core/sobre.html')

def csrf_failure(request, reason=""):
    # Pode até logar o erro se quiser, mas aqui só mostramos a tela bonita
    return render(request, 'core/403_csrf.html')