from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Equipe(models.Model):
    nome = models.CharField(max_length=100)
    data_criação = models.DateTimeField(auto_now_add=True)
    membros = models.ManyToManyField(User, related_name='equipes', blank=True)

    def __str__(self):
        return self.nome

class TagCategory(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "Categoria de Tag"
        verbose_name_plural = "Categorias de Tags"

class Tag(models.Model):
    nome = models.CharField(max_length=50, unique=True, help_text="Ex: Nativa, Frutífera, Ornamental")
    cor_fundo = models.CharField(max_length=7, default="#E9ECEF", help_text="Cor de fundo da tag (formato HEX, ex: #E9ECEF)")
    cor_texto = models.CharField(max_length=7, default="#495057", help_text="Cor do texto da tag (formato HEX, ex: #495057)")
    categoria = models.ForeignKey(TagCategory, on_delete=models.CASCADE, related_name="tags", null=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['categoria__nome', 'nome']

class Especie(models.Model):
    nome_popular = models.CharField(max_length=150, unique=True)
    nome_cientifico =  models.CharField(max_length=150, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    imagem = models.ImageField(upload_to='especies_fotos/', blank=True, null=True, help_text="Foto que aparecerá no card do catálogo.")
    tags = models.ManyToManyField(Tag, blank=True, related_name="especies")

    def __str__(self):
        return self.nome_popular

class InstanciaArvore(models.Model):
    ESTADO_SAUDE_CHOICES = (
        ('BOA', 'Boa'),
        ('REGULAR', 'Regular'),
        ('RUIM', 'Ruim'),
        ('MORTA', 'Morta'),  
    )
    especie = models.ForeignKey(Especie, on_delete=models.PROTECT, related_name='instancias')
    latitude = models.FloatField()
    longitude = models.FloatField()
    estado_saude = models.CharField(
        max_length=10,
        choices=ESTADO_SAUDE_CHOICES,
        default='BOA',
        blank=True,
        null=True
    )
    data_plantio = models.DateField(
        blank=True, null=True, default=timezone.now
    )
    # =======================================================================
    # LINHA ADICIONADA AQUI
    # =======================================================================
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        # Corrigindo uma pequena digitação aqui também, de 'especies' para 'especie'
        return f'{self.especie.nome_popular} #{self.id}'

class Solicitacao(models.Model):
    TIPO_CHOICES = (
        ('SUGESTAO', 'Sugestão'),
        ('DENUNCIA', 'Denúncia'),
    )
    STATUS_CHOICES = (
        ('EM_ABERTO', 'Em Aberto'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('FINALIZADO', 'Finalizado'),
        ('RECUSADO', 'Recusado'),
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='EM_ABERTO')
    descricao = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    cidadao = models.ForeignKey(User, on_delete=models.CASCADE)
    equipe_delegada = models.ForeignKey(Equipe, on_delete=models.SET_NULL, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f'{self.get_tipo_display()} #{self.id} - {self.status}'

class ImagemSolicitacao(models.Model):
    solicitacao = models.ForeignKey(Solicitacao, related_name='imagens', on_delete=models.CASCADE)
    imagem = models.ImageField(upload_to='solicitacoes/')

    def __str__(self):
        return f"Imagem para a Solicitação #{self.solicitacao.id}"

class Projeto(models.Model):
    MAPA_CHOICES = (
        ('CARTOGRAFICO', 'Cartográfico'),
        ('CALOR', 'Mapa de Calor'),
        ('SATELITE', 'Satélite'),
        ('USO_SOLO', 'Uso de Solo'),
        ('EM_BRANCO', 'Em Branco'),
    )
    nome = models.CharField(max_length=200)
    tipo_mapa = models.CharField(max_length=20, choices=MAPA_CHOICES, default='CARTOGRAFICO')
    cidade = models.CharField(max_length=100)
    data_criação = models.DateTimeField(auto_now_add=True)
    colaboradores = models.ManyToManyField(User, related_name='projetos_colaborados', blank=True)
    editores = models.ManyToManyField(User, related_name='projetos_editados', blank=True)
    visualizadores = models.ManyToManyField(User, related_name='projetos_visualizados', blank=True)

    def __str__(self):
        return self.nome

class Area(models.Model):
    TIPO_AREA_CHOICES = (
        ('PUBLICA', 'Pública'),
        ('PRIVADA', 'Privada'),
        ('ENCOSTA', 'Encosta'),
        ('FLORESTA', 'Floresta'),
        ('CANTEIRO', 'Canteiro'),
    )
    STATUS_AREA_CHOICES = (
        ('PLANEJANDO', 'Planejando'),
        ('AGUARDANDO_APROVAÇAO', 'Aguardando Aprovação'),
        ('EM_EXECUCAO', 'Em Execução'),
        ('FINALIZADO', 'Finalizado'),
        ('JA_EXISTENTE', 'Já Existente'),
    )
    TIPO_VEGETACAO_CHOICES = (
        ('NENHUMA', 'Nenhuma'),
        ('NATIVA', 'Nativa'),
        ('EXOTICA', 'Exótica'),
        ('FRUTIFERA', 'Frutífera'),
        ('ORNAMENTAL', 'Ornamental'),
        ('MISTA', 'Mista'),
    )

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='area')
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=50, choices=TIPO_AREA_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_AREA_CHOICES)
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='area_responsaveis')
    tipo_vegetacao = models.CharField(max_length=50, choices=TIPO_VEGETACAO_CHOICES)
    especies = models.ManyToManyField(Especie, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    geom = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f'{self.nome} ({self.projeto.nome})'
    
class CidadePermitida(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "Cidade Permitida"
        verbose_name_plural = "Cidades Permitidas"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    imagem = models.ImageField(default='profile_pics/default.jpg', upload_to='profile_pics')
    
    # LINHA PRINCIPAL - A cidade onde o cara mora
    cidade_principal = models.ForeignKey(
        CidadePermitida, 
        on_delete=models.SET_NULL, # Se a cidade for apagada, não apaga o perfil
        null=True, 
        blank=True,
        related_name="usuarios_residentes"
    )

    # LINHAS EXTRAS - As outras cidades que ele pode ver
    cidades_secundarias = models.ManyToManyField(
        CidadePermitida,
        blank=True,
        related_name="usuarios_visitantes"
    )

    def __str__(self):
        return f'Perfil de {self.user.username}'
    
