from django.urls import path
from . import views 
from .views import (solicitacao_list, solicitacao_create, solicitacao_update, arvore_list, 
arvore_create, arvore_update, mapa_view, salvar_area, cadastro_view)
from django.contrib.auth import views as auth_views




urlpatterns = [
    path('', solicitacao_list, name='home'),
    path('solicitacoes/', views.solicitacao_list, name='solicitacao_list'),
    path('solicitacoes/nova/', solicitacao_create, name='solicitacao_create'),
    path('solicitacoes/<int:pk>/editar/', solicitacao_update, name='solicitacao_update'),
    path('arvores/', arvore_list, name='arvore_list'),
    path('arvores/nova/', arvore_create, name='arvore_create'),
    path('arvores/<int:pk>/editar/', arvore_update, name='arvore_update'),
    path('mapa/', mapa_view, name='mapa'),
    path('api/salvar_area/', salvar_area, name='salvar_area'),
    path('cadastro/', cadastro_view, name='cadastro'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

