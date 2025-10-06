# Arquivo: core/admin.py (Versão Completa e Unificada)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Juntando todos os seus models e os que faltavam em um lugar só
from .models import (
    Equipe, InstanciaArvore, Solicitacao, Projeto, Area, Especie, Tag,
    Profile, CidadePermitida, TagCategory
)


# --- SEUS ADMINS CUSTOMIZADOS (MANTIDOS E ORGANIZADOS) ---

@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_tipo_display','status','cidadao','data_criacao', 'latitude', 'longitude')
    list_filter = ('status','tipo')
    search_fields = ('descricao','cidadao__username')

@admin.register(InstanciaArvore)
class InstanciaArvoreAdmin(admin.ModelAdmin):
    list_display = ('get_especie_nome', 'estado_saude', 'data_plantio', 'latitude', 'longitude')
    search_fields = ('especie__nome_popular', 'especie__nome_cientifico') 
    list_filter = ('estado_saude', 'especie')

    def get_especie_nome(self, obj):
        return obj.especie.nome_popular
    get_especie_nome.short_description = 'Espécie' 

@admin.register(Especie)
class EspecieAdmin(admin.ModelAdmin):
    list_display = ('nome_popular', 'nome_cientifico')
    search_fields = ('nome_popular', 'nome_cientifico')
    filter_horizontal = ('tags',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cor_fundo', 'cor_texto')
    search_fields = ('nome',)


# --- NOVOS ADMINS PARA AS CIDADES E PERFIL (A PARTE QUE FALTAVA) ---

@admin.register(CidadePermitida)
class CidadePermitidaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Perfil do Usuário (com Cidades Permitidas)'

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


# --- REGISTRO FINAL DOS MODELOS ---

# Re-registra o User Admin pra incluir o Profile lá dentro
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Registra os modelos que não precisam de customização especial
admin.site.register(Equipe)
admin.site.register(Projeto)
admin.site.register(Area)
admin.site.register(TagCategory) # Registrando a Categoria de Tag que estava no seu models.py