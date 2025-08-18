from django.urls import path
from . import views 
from .views import solicitacao_list, solicitacao_create


urlpatterns = [
    path('solicitacoes/', views.solicitacao_list, name='solicitacao_list'),

    path('', solicitacao_list, name='home'),

    path('solicitacoes/nova/', solicitacao_create, name='solicitacao_create'),
]

