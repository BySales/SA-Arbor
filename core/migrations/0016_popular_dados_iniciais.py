

from django.db import migrations

CATEGORIAS = ["Origens", "Portes", "Usos", "Raízes"]

TAGS_INICIAIS = [
    # ... (cole aquela lista gigante de tags aqui) ...
    {'nome': 'Nativa', 'categoria': 'Origens', 'cor_fundo': '#E6F3EB', 'cor_texto': '#1E5943'},
    {'nome': 'Exótica', 'categoria': 'Origens', 'cor_fundo': '#EAEAF9', 'cor_texto': '#6f42c1'},
    {'nome': 'Pequena', 'categoria': 'Portes', 'cor_fundo': '#EAF4F9', 'cor_texto': '#17A2B8'},
    {'nome': 'Média', 'categoria': 'Portes', 'cor_fundo': '#E6F0FF', 'cor_texto': '#007bff'},
    {'nome': 'Grande', 'categoria': 'Portes', 'cor_fundo': '#E1E4F5', 'cor_texto': '#435ebe'},
    {'nome': 'Ornamental', 'categoria': 'Usos', 'cor_fundo': '#F8EAEA', 'cor_texto': '#DC3545'},
    {'nome': 'Frutífera', 'categoria': 'Usos', 'cor_fundo': '#FFF8E1', 'cor_texto': '#d69d00'},
    {'nome': 'Sombreamento', 'categoria': 'Usos', 'cor_fundo': '#EBF8EE', 'cor_texto': '#28A745'},
    {'nome': 'Quebra-vento', 'categoria': 'Usos', 'cor_fundo': '#F8F9FA', 'cor_texto': '#6C757D'},
    {'nome': 'Raiz Agressiva', 'categoria': 'Raízes', 'cor_fundo': '#F5C6CB', 'cor_texto': '#721c24'},
    {'nome': 'Raiz Não-Agressiva', 'categoria': 'Raízes', 'cor_fundo': '#D4EDDA', 'cor_texto': '#155724'},
]

def criar_tags_e_categorias(apps, schema_editor):
    TagCategory = apps.get_model('core', 'TagCategory')
    Tag = apps.get_model('core', 'Tag')
    for nome_cat in CATEGORIAS:
        TagCategory.objects.get_or_create(nome=nome_cat)
    for tag_data in TAGS_INICIAIS:
        categoria_obj = TagCategory.objects.get(nome=tag_data['categoria'])
        Tag.objects.get_or_create(
            nome=tag_data['nome'],
            defaults={
                'categoria': categoria_obj,
                'cor_fundo': tag_data['cor_fundo'],
                'cor_texto': tag_data['cor_texto']
            }
        )

class Migration(migrations.Migration):
    # AGORA A DEPENDÊNCIA ESTÁ CORRETA E GARANTIDA
    dependencies = [
        # Coloque aqui o nome do arquivo que você criou no PASSO 2
        ('core', '0015_tag_tagcategory_especie_imagem_especie_tags_and_more'), 
    ]
    operations = [
        migrations.RunPython(criar_tags_e_categorias),
    ]