import json, urllib.request

URL_SP = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-35-mun.json"
BAIXADA = {
    "Bertioga","Cubatão","Guarujá","Itanhaém",
    "Mongaguá","Peruíbe","Praia Grande","Santos","São Vicente"
}

def get_name(props):
    for k in ("name","nome","NM_MUNICIPIO","NM_MUN","municipio","city"):
        if k in props and props[k]:
            return str(props[k])
    return None

with urllib.request.urlopen(URL_SP, timeout=60) as r:
    sp = json.load(r)

feats = []
for f in sp.get("features", []):
    props = f.get("properties", {})
    nome = get_name(props)
    if not nome:
        continue
    if nome.strip().casefold() in {n.casefold() for n in BAIXADA}:
        feats.append(f)

out = {"type":"FeatureCollection","features":feats}
with open("core/data/baixada_santista.geojson","w",encoding="utf-8") as w:
    json.dump(out, w, ensure_ascii=False)

print(f"✅ Gerado core/data/baixada_santista.geojson com {len(feats)} municípios.")
