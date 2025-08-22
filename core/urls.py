from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    solicitacao_list, solicitacao_create, solicitacao_update, solicitacao_delete,
    arvore_list, arvore_create, arvore_update, arvore_delete,
    mapa_view,
    cadastro_view,
    salvar_area,
    area_manage_api # Nossa nova super view
)

urlpatterns = [
    # --- URLs da Homepage ---
    path('', solicitacao_list, name='home'),

    # --- URLs de Solicitação ---
    path('solicitacoes/', solicitacao_list, name='solicitacao_list'),
    path('solicitacoes/nova/', solicitacao_create, name='solicitacao_create'),
    path('solicitacoes/<int:pk>/editar/', solicitacao_update, name='solicitacao_update'),
    path('solicitacoes/<int:pk>/deletar/', solicitacao_delete, name='solicitacao_delete'),

    # --- URLs de Árvore ---
    path('arvores/', arvore_list, name='arvore_list'),
    path('arvores/nova/', arvore_create, name='arvore_create'),
    path('arvores/<int:pk>/editar/', arvore_update, name='arvore_update'),
    path('arvores/<int:pk>/deletar/', arvore_delete, name='arvore_delete'),

    # --- URLs do Mapa ---
    path('mapa/', mapa_view, name='mapa'),

    # --- URLs de Autenticação ---
    path('cadastro/', cadastro_view, name='cadastro'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # --- API Endpoints ---
    path('api/salvar_area/', salvar_area, name='salvar_area'),
    # A NOVA ROTA QUE FAZ TUDO (GET, PUT, DELETE) PARA UMA ÁREA ESPECÍFICA
    path('api/areas/<int:pk>/', area_manage_api, name='area_manage_api'),
]