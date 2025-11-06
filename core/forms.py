from django import forms
from django.contrib.auth.models import User
# PRECISA importar UserCreationForm aqui
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm 
from .models import (
    Solicitacao, Area, Profile, Equipe, Especie, Tag, CidadePermitida
)


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
                    # Correção: Verificar se p1_lat == p2_lat ANTES de calcular lon_intersection
                    # E tratar a linha vertical
                    if p1_lat == p2_lat:
                         if p1_lon == p2_lon: # Ponto, não linha
                             if lat == p1_lat and lon == p1_lon:
                                 inside = True # Considera ponto na borda como dentro
                                 break
                         elif lon <= p1_lon: # Linha horizontal
                             inside = not inside
                    elif p1_lon == p2_lon or lon <= lon_intersection:
                         inside = not inside
        p1_lat, p1_lon = p2_lat, p2_lon
        
    return inside

# forms.py

class SolicitacaoForm(forms.ModelForm):
    # ... (seus campos 'imagens' e 'especie_plantada' continuam iguais) ...
    imagens = forms.FileField(
        required=False,
        label='Anexar imagens (max 10)',
        widget=forms.FileInput(attrs={'class': 'd-none'})
    )
    
    especie_plantada = forms.ModelChoiceField(
        queryset=Especie.objects.all().order_by('nome_popular'), 
        required=False, 
        label="Espécie Plantada (Obrigatório se 'Finalizado')",
        widget=forms.Select(attrs={'class': 'form-select form-control-custom'}),
        empty_label="Selecione a espécie..."
    )


    def __init__(self, *args, user, **kwargs):
        # ... (seu __init__ continua igualzinho) ...
        super().__init__(*args, **kwargs)

        self.fields['cidade'].empty_label = "Selecione a cidade..."
        self.fields['equipe_delegada'].empty_label = "Selecione a equipe..."

        # 2. Para TIPO (que é um ChoiceField, tem que fazer uma manobra)
        # Pega as opções atuais
        tipo_choices = list(self.fields['tipo'].choices)
        # Se a primeira opção for vazia (o "---------"), a gente arranca ela
        if tipo_choices and tipo_choices[0][0] == '':
             tipo_choices.pop(0)
        # E coloca a nossa bonitona no lugar
        self.fields['tipo'].choices = [('', 'Selecione o tipo...')] + tipo_choices

        # 3. Aproveitando, vamos fazer pro CATEGORIA também (se ele aparecer de prima)
        cat_choices = list(self.fields['categoria'].choices)
        if cat_choices and cat_choices[0][0] == '':
             cat_choices.pop(0)
        self.fields['categoria'].choices = [('', 'Selecione o detalhe...')] + cat_choices

        profile = user.profile
        cidades_ids = []
        if profile.cidade_principal:
            cidades_ids.append(profile.cidade_principal.id)
        cidades_ids.extend(profile.cidades_secundarias.all().values_list('id', flat=True))

        cidades_permitidas = CidadePermitida.objects.filter(id__in=set(cidades_ids)).order_by('nome')
        self.fields['cidade'].queryset = cidades_permitidas
        
        if len(cidades_permitidas) == 1:
            self.fields['cidade'].initial = cidades_permitidas.first()
        elif not self.instance.pk and profile.cidade_principal:
             self.fields['cidade'].initial = profile.cidade_principal

    def clean(self):
        # ... (seu clean continua igualzinho) ...
        cleaned_data = super().clean()
        status_atual = cleaned_data.get("status")
        categoria = cleaned_data.get("categoria")
        especie_selecionada = cleaned_data.get("especie_plantada")
        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude")
        cidade = cleaned_data.get("cidade")
        motivo_recusa = cleaned_data.get("motivo_recusa")

        if status_atual == 'FINALIZADO' and categoria in ['PLANTIO', 'TROCA_LOCAL']:
            if not especie_selecionada:
                self.add_error('especie_plantada', 'Para finalizar um Plantio ou Troca de Local, informe a espécie.')
            
            if not especie_selecionada:
                self.add_error('especie_plantada', 'Você deve selecionar a espécie que foi plantada para poder finalizar.')
            if not latitude or not longitude:
                self.add_error(None, 'Não é possível finalizar. Volte à Etapa 2 e marque a localização no mapa.')
                if not latitude:
                    self.add_error('latitude', 'A localização é obrigatória para finalizar.')
                if not longitude:
                    self.add_error('longitude', 'A localização é obrigatória para finalizar.')

        if status_atual == 'RECUSADO':
            if not motivo_recusa:
                self.add_error('motivo_recusa', 'Por favor, informe o motivo da recusa para o cidadão.')

        if status_atual != 'RECUSADO' and motivo_recusa:
             cleaned_data['motivo_recusa'] = None
        
        elif status_atual != 'FINALIZADO' and especie_selecionada:
            cleaned_data['especie_plantada'] = None
        
        if all([cidade, latitude, longitude]):
            if not cidade.geom or 'coordinates' not in cidade.geom:
                pass
            else:
                ponto_marcado = (latitude, longitude)
                coords_list = []
                if cidade.geom['type'] == 'Polygon':
                    coords_list = cidade.geom['coordinates'][0]
                elif cidade.geom['type'] == 'MultiPolygon':
                      if cidade.geom['coordinates'] and cidade.geom['coordinates'][0]:
                           coords_list = cidade.geom['coordinates'][0][0] 
                
                if coords_list:
                    limites_da_cidade_lon_lat = coords_list
                    limites_da_cidade_corrigido = [(lat, lon) for lon, lat in limites_da_cidade_lon_lat]

                    if not is_point_in_polygon(ponto_marcado, limites_da_cidade_corrigido):
                        self.add_error('latitude', f"O ponto marcado no mapa (Etapa 2) não parece estar dentro dos limites de {cidade.nome}.")
                else:
                      print(f"AVISO: Geometria da cidade {cidade.nome} (ID: {cidade.id}) não é um Polygon ou MultiPolygon simples. Validação de ponto pulada.")

        return cleaned_data

    def clean_latitude(self):
        # ... (igual) ...
        latitude = self.cleaned_data.get('latitude')
        if latitude == '': return None 
        try:
             if latitude is not None: return float(str(latitude).replace(',', '.'))
        except (ValueError, TypeError): raise forms.ValidationError("Informe um número válido para latitude.")
        return latitude 

    def clean_longitude(self):
        # ... (igual) ...
        longitude = self.cleaned_data.get('longitude')
        if longitude == '': return None
        try:
            if longitude is not None: return float(str(longitude).replace(',', '.'))
        except (ValueError, TypeError): raise forms.ValidationError("Informe um número válido para longitude.")
        return longitude

    class Meta:
        model = Solicitacao
        fields = ['cidade', 'tipo', 'categoria', 'descricao', 'latitude', 'longitude', 'status', 'equipe_delegada', 'motivo_recusa']
        
        widgets = {
            'cidade': forms.Select(attrs={'class': 'form-select form-control-custom'}),
            # 🔥 Adicionei o ID 'id_tipo' aqui pra garantir que o JS ache ele
            'tipo': forms.Select(attrs={'class': 'form-select form-control-custom', 'id': 'id_tipo'}),
            # 🔥 Adicionei o widget da 'categoria' com o ID 'id_categoria'
            'categoria': forms.Select(attrs={'class': 'form-select form-control-custom', 'id': 'id_categoria'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control form-control-custom', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select form-control-custom', 'id': 'id_status'}),
            'equipe_delegada': forms.Select(attrs={'class': 'form-select form-control-custom'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'motivo_recusa': forms.Textarea(attrs={'class': 'form-control form-control-custom', 'rows': 3}),
        }
        
        labels = {
            'cidade': 'Cidade da Solicitação',
            'tipo': 'Tipo',
            # 🔥 Adicionei o label personalizado
            'categoria': 'Detalhe a sua Solicitação',
            'descricao': 'Descrição',
            'status': 'Status da Solicitação',
            'equipe_delegada': 'Delegar para a Equipe',
            'imagens': 'Anexar imagens'
        }

class EspecieForm(forms.ModelForm):
    class Meta:
        model = Especie
        fields = ['nome_popular', 'nome_cientifico', 'descricao', 'imagem', 'tags']
        labels = {
            'nome_popular': 'Nome Popular',
            'nome_cientifico': 'Nome Científico',
            'descricao': 'Descrição da Espécie',
            'imagem': 'Foto da Espécie',
            'tags': 'Tags (Categorias)',
        }
        widgets = {
            'nome_popular': forms.TextInput(attrs={'class': 'form-control-custom', 'autocomplete': 'off'}),
            'nome_cientifico': forms.TextInput(attrs={'class': 'form-control-custom', 'autocomplete': 'off'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control-custom', 'autocomplete': 'off', 'rows': 4}),
            'imagem': forms.ClearableFileInput(attrs={'class': 'd-none'}), # Esconde input padrão
            'tags': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }

class AreaForm(forms.ModelForm):
    class Meta: 
        model = Area
        fields = ['nome', 'tipo', 'status', 'especies']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control form-control-custom', 'autocomplete': 'off'}),
            'tipo': forms.Select(attrs={'class': 'form-select form-control-custom'}),
            'status': forms.Select(attrs={'class': 'form-select form-control-custom'}),
            'especies': forms.SelectMultiple(attrs={'class': 'form-select form-control-custom select2-multiple', 'style': 'width: 100%;'}),
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': 'Nome de Usuário (não pode ser alterado)',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'Email de Contato',
        }
        widgets = {
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
        # Filtra cidades que têm geometria definida
        qs = CidadePermitida.objects.filter(geom__isnull=False).order_by('nome')
        self.fields['cidade_principal'].queryset = qs
        self.fields['cidades_secundarias'].queryset = qs

class EquipeForm(forms.ModelForm):
    class Meta:
        model = Equipe
        fields = ['nome', 'membros']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control-custom', 'autocomplete': 'off'}),
            'membros': forms.CheckboxSelectMultiple, # Bootstrap estiliza bem
        }
    
    # Filtra para mostrar apenas usuários que são 'staff'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['membros'].queryset = User.objects.filter(is_staff=True).order_by('username')


class CadastroCidadaoForm(UserCreationForm):
    cidade_principal = forms.ModelChoiceField(
        queryset=CidadePermitida.objects.filter(geom__isnull=False).order_by('nome'),
        label="Sua Cidade Principal",
        required=True,
        empty_label="Selecione sua cidade"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cidade_principal'].widget.attrs.update({'class': 'form-select form-control-custom'})

    # Método save corrigido para 'get' e 'update'
    def save(self, commit=True):
        user = super().save(commit=True) # Salva o User primeiro
        cidade = self.cleaned_data.get('cidade_principal')

        # Tenta pegar o perfil (criado pelo signal) e atualizar
        try:
            profile = user.profile 
            profile.cidade_principal = cidade
            profile.save()
        # Se não existir perfil (signal falhou ou não existe), cria na mão
        except Profile.DoesNotExist:
            Profile.objects.create(user=user, cidade_principal=cidade)
        
        return user