from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    solicitacao_list, solicitacao_create, solicitacao_update, solicitacao_delete,
    especie_list, especie_create, especie_update, especie_delete,
    mapa_view, cadastro_view, salvar_area, area_manage_api, 
    configuracoes_view, equipe_list, equipe_create, equipe_update, equipe_delete, instancia_arvore_create_api,
    search_results_view,
    obras_view,
    analisar_area_api, recuperar_senha_view, home_view
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # --- URLs da Homepage ---
    path('', home_view, name='home'),

    # --- URLs da Busca ---
    path('busca/', search_results_view, name='search_results'),

    # --- URLs de Solicitação ---
    path('solicitacoes/', solicitacao_list, name='solicitacao_list'),
    path('solicitacoes/nova/', solicitacao_create, name='solicitacao_create'),
    path('solicitacoes/<int:pk>/editar/', solicitacao_update, name='solicitacao_update'),
    path('solicitacoes/<int:pk>/deletar/', solicitacao_delete, name='solicitacao_delete'),

    # --- URLs de Espécie ---
    path('especies/', especie_list, name='especie_list'),
    path('especies/nova/', especie_create, name='especie_create'),
    path('especies/<int:pk>/editar/', especie_update, name='especie_update'),
    path('especies/<int:pk>/deletar/', especie_delete, name='especie_delete'),
    
    # --- URL da Tela de Obras ---
    path('obras/', obras_view, name='obras_list'), 

    # --- URLs do Mapa ---
    path('mapa/', mapa_view, name='mapa'),

    # --- URLs de Autenticação ---
    path('cadastro/', cadastro_view, name='cadastro'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('recuperar-senha/', recuperar_senha_view, name='recuperar_senha'),
    path('configuracoes/', configuracoes_view, name='configuracoes'),

    # --- API Endpoints ---
    path('api/instancias/nova/', instancia_arvore_create_api, name='instancia_arvore_create_api'),
    path('api/salvar_area/', salvar_area, name='salvar_area'),
    path('api/areas/<int:pk>/', area_manage_api, name='area_manage_api'),
    path('api/analisar-area/', analisar_area_api, name='analisar_area_api'), # <-- 2. ADICIONAMOS A NOVA ROTA DA API

    # --- URLs de Equipe ---
    path('equipes/', equipe_list, name='equipe_list'),
    path('equipes/nova/', equipe_create, name='equipe_create'),
    path('equipes/<int:pk>/editar/', equipe_update, name='equipe_update'),
    path('equipes/<int:pk>/deletar/', equipe_delete, name='equipe_delete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)