# seu_app/admin.py

from django.contrib import admin
# IMPORTAMOS O NOVO MODELO 'TAG' AQUI
from .models import Equipe, InstanciaArvore, Solicitacao, Projeto, Area, Especie, Tag

class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_tipo_display','status','cidadao','data_criacao', 'latitude', 'longitude')
    list_filter = ('status','tipo')
    search_fields = ('descricao','cidadao__username')

class InstanciaArvoreAdmin(admin.ModelAdmin):
    list_display = ('get_especie_nome', 'estado_saude', 'data_plantio', 'latitude', 'longitude')
    search_fields = ('especie__nome_popular', 'especie__nome_cientifico') 
    list_filter = ('estado_saude', 'especie')

    def get_especie_nome(self, obj):
        return obj.especie.nome_popular
    get_especie_nome.short_description = 'Espécie' 

class EspecieAdmin(admin.ModelAdmin):
    # Adicionamos o campo de imagem para fácil visualização
    list_display = ('nome_popular', 'nome_cientifico')
    search_fields = ('nome_popular', 'nome_cientifico')
    # Filtro para facilitar o gerenciamento das tags no futuro
    filter_horizontal = ('tags',)

# --- CLASSE NOVA PARA O ADMIN DE TAGS ---
class TagAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cor_fundo', 'cor_texto')
    search_fields = ('nome',)


# REGISTRO DOS MODELOS
admin.site.register(Equipe)
admin.site.register(Projeto)
admin.site.register(Area)
admin.site.register(Solicitacao, SolicitacaoAdmin)
admin.site.register(Especie, EspecieAdmin)
admin.site.register(InstanciaArvore, InstanciaArvoreAdmin)
admin.site.register(Tag, TagAdmin) # <<< REGISTRO DA TAG