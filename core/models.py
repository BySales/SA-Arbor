from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Equipe(models.Model):
    nome = models.CharField(max_length=100)
    data_criação = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome
    
class Arvore(models.Model):
    nome_popular = models.CharField(max_length=150)
    nome_cientifico = models.CharField(max_length=150, blank=True, null=True)
    descricao = models.TextField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.nome_popular
    
class Solicitacao(models.Model):
    TIPO_CHOICES = (
        ('SUGESTAO', 'Sugestão'),
        ('DENUNCIA', 'Denúncia'),
    )
    STATUS_CHOICES = (
        ('EM_ABERTO', 'Em Aberto'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('FINALIZADO', 'Finalizado'),
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='EM_ABERTO')
    descricao = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    cidadao = models.ForeignKey(User, on_delete=models.CASCADE)
    equipe_delegada = models.ForeignKey(Equipe, on_delete=models.SET_NULL, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    imagem = models.ImageField(upload_to='solicitacoes/', null=True, blank=True)

    def __str__(self):
        return f'{self.get_tipo_display()} #{self.id} - {self.status}'
    
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
    especies = models.ManyToManyField(Arvore, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    geom = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f'{self.nome} ({self.projeto.nome})'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    imagem = models.ImageField(default='profile_pics/default.jpg', upload_to='profile_pics')

    def __str__(self):
        return f'Perfil de {self.user.username}'