from .models import Notificacao

def notificacoes_context(request):
    # Se o maluco não tá logado, não tem o que fazer
    if not request.user.is_authenticated:
        return {}

    # Busca as notificações NÃO LIDAS do maluco logado
    notificacoes_nao_lidas = Notificacao.objects.filter(
        usuario=request.user, 
        lida=False
    ).order_by('-data_criacao') # Pega as 5 mais novas
    
    # Pega a CONTAGEM total
    count = notificacoes_nao_lidas.count()

    # Manda essa contagem e a lista pra TODOS os templates
    return {
        'notificacoes_nao_lidas': notificacoes_nao_lidas[:5], # Manda só as 5 primeiras
        'notificacoes_count': count
    }