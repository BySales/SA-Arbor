from django.contrib import admin
from .models import Equipe, Arvore, Solicitacao, Projeto, Area
# Register your models here.

class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_tipo_display','status','cidadao','data_criacao')
    list_filter = ('status','tipo')
    search_fields = ('descricao','cidadao__username')

class ArvoreAdmin(admin.ModelAdmin):
    list_display = ('nome_popular', 'nome_cientifico', 'latitude', 'longitude')
    search_fields = ('nome_popular', 'nome_cientifico')

admin.site.register(Equipe)
admin.site.register(Projeto)
admin.site.register(Area)
admin.site.register(Solicitacao, SolicitacaoAdmin)
admin.site.register(Arvore, ArvoreAdmin)