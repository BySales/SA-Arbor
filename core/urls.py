from django.urls import path
from . import views 
from .views import (solicitacao_list, solicitacao_create, solicitacao_update, arvore_list, 
arvore_create, arvore_update, mapa_view, salvar_area, cadastro_view, solicitacao_delete, arvore_delete)
from django.contrib.auth import views as auth_views




urlpatterns = [
    # --- URLs da Home ---
    path('', solicitacao_list, name='home'),

# --- URLs de Solicitação ---
    path('solicitacoes/', views.solicitacao_list, name='solicitacao_list'),
    path('solicitacoes/nova/', solicitacao_create, name='solicitacao_create'),
    path('solicitacoes/<int:pk>/deletar/', solicitacao_delete, name='solicitacao_delete'),
    path('solicitacoes/<int:pk>/editar/', solicitacao_update, name='solicitacao_update'),

# --- URLs de Árvore ---
    path('arvores/', arvore_list, name='arvore_list'),
    path('arvores/nova/', arvore_create, name='arvore_create'),
    path('arvores/<int:pk>/editar/', arvore_update, name='arvore_update'),
    path('arvores/<int:pk>/deletar/', arvore_delete, name='arvore_delete'),

# --- URLs de Mapa ---
    path('mapa/', mapa_view, name='mapa'),

# --- URLs de Login/Cadastro/Logout ---
    path('api/salvar_area/', salvar_area, name='salvar_area'),
    path('cadastro/', cadastro_view, name='cadastro'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

