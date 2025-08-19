from django.urls import path
from . import views 
from .views import solicitacao_list, solicitacao_create, solicitacao_update, arvore_list, arvore_create, arvore_update, mapa_view



urlpatterns = [
    path('', solicitacao_list, name='home'),
    path('solicitacoes/', views.solicitacao_list, name='solicitacao_list'),
    path('solicitacoes/nova/', solicitacao_create, name='solicitacao_create'),
    path('solicitacoes/<int:pk>/editar/', solicitacao_update, name='solicitacao_update'),
    path('arvores/', arvore_list, name='arvore_list'),
    path('arvores/nova/', arvore_create, name='arvore_create'),
    path('arvores/<int:pk>/editar/', arvore_update, name='arvore_update'),
    path('mapa/', mapa_view, name='mapa')
]

