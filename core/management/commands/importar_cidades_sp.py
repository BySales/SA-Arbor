import json
from django.core.management.base import BaseCommand, CommandError
from core.models import CidadePermitida

class Command(BaseCommand):
    help = "Importa cidades de SP de um GeoJSON local para CidadePermitida (nome + geom)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--arquivo",
            default="core/data/baixada_santista.geojson",  # ⬅ default atualizado
            help="Caminho do GeoJSON (FeatureCollection) com properties de nome (ex.: name/NM_MUNICIPIO/nome) e geometry."
        )
        parser.add_argument(
            "--so",
            nargs="*",
            help="Opcional: lista de nomes de cidades para importar (ex.: --so 'Santos' 'São Vicente')."
        )

    def handle(self, *args, **opts):
        caminho = opts["arquivo"]
        filtro = set(n.lower() for n in (opts["so"] or []))

        try:
            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise CommandError(f"Falha ao ler {caminho}: {e}")

        if data.get("type") != "FeatureCollection":
            raise CommandError("GeoJSON inválido: esperado FeatureCollection.")

        # helper para achar o nome em diferentes chaves
        def get_nome(props):
            for k in ("name", "nome", "NM_MUNICIPIO", "NM_MUN", "municipio", "city", "Description", "description"):
                val = props.get(k)
                if val:
                    return str(val)
            return None

        count = 0
        for feat in data.get("features", []):
            props = feat.get("properties", {}) or {}
            geom = feat.get("geometry")
            nome = get_nome(props)
            if not nome or not geom:
                continue

            if filtro and nome.lower() not in filtro:
                continue

            CidadePermitida.objects.update_or_create(
                nome=nome,
                defaults={"geom": geom}
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Importadas/atualizadas {count} cidades."))
