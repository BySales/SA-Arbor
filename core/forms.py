from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from .models import Solicitacao, Area, Profile, Equipe, Especie, Tag, CidadePermitida


def is_point_in_polygon(point, polygon):
    """
    Verifica se um ponto (lat, lon) está dentro de um polígono.
    Usa o algoritmo Ray Casting.
    """
    lat, lon = point
    n = len(polygon)
    inside = False
    
    p1_lat, p1_lon = polygon[0]
    for i in range(n + 1):
        p2_lat, p2_lon = polygon[i % n]
        if lat > min(p1_lat, p2_lat):
            if lat <= max(p1_lat, p2_lat):
                if lon <= max(p1_lon, p2_lon):
                    if p1_lat != p2_lat:
                        lon_intersection = (lat - p1_lat) * (p2_lon - p1_lon) / (p2_lat - p1_lat) + p1_lon
                    if p1_lon == p2_lon or lon <= lon_intersection:
                        inside = not inside
        p1_lat, p1_lon = p2_lat, p2_lon
        
    return inside

class SolicitacaoForm(forms.ModelForm):
    imagens = forms.ImageField(
        required=False,
        label='Anexar imagens (segure CTRL para selecionar várias)'
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['imagens'].widget.attrs.update({'multiple': True})
        
        profile = user.profile
        cidades_ids = []
        if profile.cidade_principal:
            cidades_ids.append(profile.cidade_principal.id)
        cidades_ids.extend(profile.cidades_secundarias.all().values_list('id', flat=True))

        cidades_permitidas = CidadePermitida.objects.filter(id__in=set(cidades_ids)).order_by('nome')
        self.fields['cidade'].queryset = cidades_permitidas
        
        if len(cidades_permitidas) == 1:
            self.fields['cidade'].initial = cidades_permitidas.first()

    # ======================================================
    # 2. O TREINAMENTO AVANÇADO DO FISCAL
    # Ensinamos ele a validar o CEP vs. Endereço
    # ======================================================
    def clean(self):
        cleaned_data = super().clean()
        cidade = cleaned_data.get("cidade")
        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude")

        # Se a cidade, lat ou lon não foram preenchidos, outros erros já vão aparecer.
        # A gente só age se tiver os três pra comparar.
        if not all([cidade, latitude, longitude]):
            return cleaned_data

        # Se a cidade escolhida não tem um mapa cadastrado, não tem como validar.
        if not cidade.geom or 'coordinates' not in cidade.geom:
            return cleaned_data
        
        # Prepara os dados para a nossa ferramenta "GPS"
        ponto_marcado = (latitude, longitude)
        limites_da_cidade_lon_lat = cidade.geom['coordinates'][0]
        
        # O GeoJSON guarda [longitude, latitude], mas nossa função espera (latitude, longitude).
        # A gente inverte a ordem pra bater certinho.
        limites_da_cidade_corrigido = [(lat, lon) for lon, lat in limites_da_cidade_lon_lat]

        # A hora da verdade: o alfinete está dentro do mapa da cidade?
        if not is_point_in_polygon(ponto_marcado, limites_da_cidade_corrigido):
            # Se não estiver, o fiscal barra a operação e manda a bronca!
            raise forms.ValidationError(
                f"O ponto marcado no mapa não está dentro dos limites de {cidade.nome}. "
                "Por favor, ajuste o pino para o local correto ou selecione a cidade correspondente."
            )
        
        # Se chegou até aqui, é porque tá tudo certo. Pode seguir.
        return cleaned_data

    class Meta:
        model = Solicitacao
        fields = ['cidade', 'tipo', 'descricao', 'latitude', 'longitude', 'status', 'equipe_delegada']
        
        widgets = {
            'cidade': forms.Select(attrs={'class': 'form-select form-control-custom'}),
            'tipo': forms.Select(attrs={'class': 'form-select form-control-custom'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control form-control-custom', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select form-control-custom'}),
            'equipe_delegada': forms.Select(attrs={'class': 'form-select form-control-custom'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
        
        labels = {
            'cidade': 'Cidade da Solicitação',
            'tipo': 'Tipo',
            'descricao': 'Descrição',
            'status': 'Status da Solicitação',
            'equipe_delegada': 'Delegar para a Equipe',
            'imagens': 'Anexar imagens'
        }

class EspecieForm(forms.ModelForm):
    class Meta:
        model = Especie
        # 1. Adicionamos os novos campos na lista
        fields = ['nome_popular', 'nome_cientifico', 'descricao', 'imagem', 'tags']
        
        # 2. Adicionamos os labels para os novos campos
        labels = {
            'nome_popular': 'Nome Popular',
            'nome_cientifico': 'Nome Científico',
            'descricao': 'Descrição da Espécie',
            'imagem': 'Foto da Espécie',
            'tags': 'Tags (Categorias)',
        }

        # 3. Definimos os widgets (a aparência) de cada campo
        widgets = {
            'nome_popular': forms.TextInput(attrs={
                'class': 'form-control-custom', 
                'autocomplete': 'off'
            }),
            'nome_cientifico': forms.TextInput(attrs={
                'class': 'form-control-custom', 
                'autocomplete': 'off'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control-custom', 
                'autocomplete': 'off', 
                'rows': 4
            }),
            # Widget especial para o campo de imagem (escondemos o input padrão)
            'imagem': forms.ClearableFileInput(attrs={'class': 'd-none'}),
            
            # Widget que transforma a seleção de tags em checkboxes
            'tags': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }

class AreaForm(forms.ModelForm):
    class Meta: 
        model = Area
        # Agora só pede os campos que realmente existem no formulário do mapa
        fields = ['nome', 'tipo', 'status', 'especies']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'autocomplete': 'off'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select form-control-custom'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select form-control-custom'
            }),
            'especies': forms.SelectMultiple(attrs={
                'class': 'form-select form-control-custom select2-multiple', 
                'style': 'width: 100%;'
            }),
        }
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        # Adicionamos o username pra ele aparecer na tela, mas não ser editável
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': 'Nome de Usuário (não pode ser alterado)',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'Email de Contato',
        }
        widgets = {
            # Deixamos o username apenas como leitura (readonly) por segurança
            'username': forms.TextInput(attrs={'class': 'form-control-custom', 'readonly': True}),
            'first_name': forms.TextInput(attrs={'class': 'form-control-custom', 'autocomplete': 'off'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control-custom', 'autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'class': 'form-control-custom', 'autocomplete': 'off'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['imagem', 'cidade_principal', 'cidades_secundarias']
        widgets = {
            'imagem': forms.FileInput(attrs={'class': 'form-control-custom'}),
            'cidade_principal': forms.Select(attrs={'class': 'form-select form-control-custom'}),
            'cidades_secundarias': forms.SelectMultiple(attrs={'class': 'form-select form-control-custom select2-multiple'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = CidadePermitida.objects.filter(geom__isnull=False).order_by('nome')
        self.fields['cidade_principal'].queryset = qs
        self.fields['cidades_secundarias'].queryset = qs

class EquipeForm(forms.ModelForm):
    class Meta:
        model = Equipe
        fields = ['nome', 'membros']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control-custom', 'autocomplete': 'off'}),
            # Checkbox não precisa da classe form-control, o Bootstrap já estiliza ele bem
            'membros':forms.CheckboxSelectMultiple,
        }

class CadastroCidadaoForm(UserCreationForm):
    # 1. CRIANDO O CAMPO NOVO
    # Esse é o campo que cria o menu 'dropdown' com as cidades.
    cidade_principal = forms.ModelChoiceField(
        # A gente só puxa cidade que tem mapa (geom__isnull=False), pra não dar B.O. lá na frente.
        queryset=CidadePermitida.objects.filter(geom__isnull=False).order_by('nome'),
        label="Sua Cidade Principal",
        required=True, # O maluco é OBRIGADO a escolher uma
        empty_label="Selecione sua cidade"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Isso aqui é só pra deixar o campo bonito, com o mesmo estilo CSS dos outros
        self.fields['cidade_principal'].widget.attrs.update({'class': 'form-select form-control-custom'})

    # 2. ENSINANDO O FORMULÁRIO A SALVAR O PERFIL (A MÁGICA)
    def save(self, commit=True):
        # 1. Salva o User. Isso vai disparar o 'signal' fantasma 
        #    que a gente suspeita que existe e que cria o Profile.
        user = super().save(commit=True) 
        
        # 2. Pega a cidade que o maluco escolheu
        cidade = self.cleaned_data.get('cidade_principal')

        # 3. A MÁGICA ATUALIZADA:
        #    Em vez de 'create' (criar), a gente vai 'get' (buscar) o perfil
        #    que o 'signal' acabou de criar, e 'update' (atualizar) ele.
        try:
            profile = user.profile  # Acessa o perfil que o signal criou
            profile.cidade_principal = cidade # Define a cidade
            profile.save() # Salva a mudança no perfil
        except Profile.DoesNotExist:
            # Se, por algum motivo, o signal não existir ou falhar,
            # a gente cria o perfil na mão, como antes (Plano B).
            Profile.objects.create(user=user, cidade_principal=cidade)
        
        return user