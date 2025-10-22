# Arquivo: core/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings  # <--- MOVIDO PRA CÁ
from django.conf.urls.static import static  # <--- MOVIDO PRA CÁ

from .views import (
    # Lista de todas as suas views
    solicitacao_list, solicitacao_create, solicitacao_update, solicitacao_delete, solicitacao_detail,
    especie_list, especie_create, especie_update, especie_delete,
    mapa_view, cadastro_view, salvar_area, area_manage_api,
    configuracoes_view, equipe_list, equipe_create, equipe_update, equipe_delete, instancia_arvore_create_api,
    search_results_view, planejamentos_view,
    analisar_area_api, recuperar_senha_view, home_view,
    AreaDeleteView,
    relatorios_view, instancia_arvore_delete_api, api_heatmap_denuncias
)
# O parêntese do 'from .views import' FECHA AQUI

# 'urlpatterns' PRECISA FICAR AQUI FORA, no nível principal
urlpatterns = [
    # --- URLs da Homepage ---
    path('', home_view, name='home'),

    # --- URLs da Busca ---
    path('busca/', search_results_view, name='search_results'),

    # --- URLs de Solicitação ---
    path('solicitacoes/', solicitacao_list, name='solicitacao_list'),
    path('solicitacoes/nova/', solicitacao_create, name='solicitacao_create'),
    path('solicitacoes/<int:pk>/', solicitacao_detail, name='solicitacao_detail'),
    path('solicitacoes/<int:pk>/editar/', solicitacao_update, name='solicitacao_update'),
    path('solicitacoes/<int:pk>/deletar/', solicitacao_delete, name='solicitacao_delete'),

    # --- URLs de Espécie ---
    path('especies/', especie_list, name='especie_list'),
    path('especies/nova/', especie_create, name='especie_create'),
    path('especies/<int:pk>/editar/', especie_update, name='especie_update'),
    path('especies/<int:pk>/deletar/', especie_delete, name='especie_delete'),

    # --- URLs de Equipe ---
    path('equipes/', equipe_list, name='equipe_list'),
    path('equipes/nova/', equipe_create, name='equipe_create'),
    path('equipes/<int:pk>/editar/', equipe_update, name='equipe_update'),
    path('equipes/<int:pk>/deletar/', equipe_delete, name='equipe_delete'),

    # --- URLs DE ÁREA ---
    path('areas/<int:pk>/delete/', AreaDeleteView.as_view(), name='area_delete'),

    # --- URLs do Mapa e APIs ---
    path('mapa/', mapa_view, name='mapa'),
    path('api/salvar_area/', salvar_area, name='salvar_area'),
    path('api/areas/<int:pk>/', area_manage_api, name='area_manage_api'),
    path('api/analisar-area/', analisar_area_api, name='analisar_area_api'),
    path('api/instancias/nova/', instancia_arvore_create_api, name='instancia_arvore_create_api'),
    path('api/arvores/<int:pk>/delete/', instancia_arvore_delete_api, name='instancia_arvore_delete_api'),
    path('api/minhas-cidades/', views.api_cidades_permitidas, name='api_cidades_usuario'),
    path('api/cidades-geo/', views.api_cidades_geo, name='api_cidades_geo'),
    path('api/heatmap/denuncias/', api_heatmap_denuncias, name='api_heatmap_denuncias'),


    # --- Outras URLs do App ---
    path('planejamentos/', planejamentos_view, name='planejamentos'),
    path('cadastro/', cadastro_view, name='cadastro'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('recuperar-senha/', recuperar_senha_view, name='recuperar_senha'),
    path('configuracoes/', configuracoes_view, name='configuracoes'),

    # --- URL DE RELATÓRIOS ---
    path('relatorios/', relatorios_view, name='relatorios'),
]

# Isso aqui também tem que ficar FORA do 'from' e DEPOIS do 'urlpatterns'
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)