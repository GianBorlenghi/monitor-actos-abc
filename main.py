import requests
import json
import os
from twilio.rest import Client

URL = "https://servicios3.abc.gob.ar/valoracion.docente/api/apd.oferta.encabezado/select"

params = {
    "q": "*:*",
    "rows": 50,
    "sort": "finoferta desc",
    "fq": "descdistrito:pergamino",
    "wt": "json"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://misservicios.abc.gob.ar/actos.publicos.digitales/",
    "Origin": "https://misservicios.abc.gob.ar"
}

r = requests.get(URL, params=params, headers=headers, timeout=30)
data = r.json()

ofertas = data["response"]["docs"]

try:
    with open("ofertas_enviadas.json", "r") as f:
        enviadas = json.load(f)
except:
    enviadas = []

nuevas = []

for o in ofertas:

    estado = o.get("estadooferta", "")
    id_oferta = str(o.get("id", ""))

    if estado == "PUBLICADA" and id_oferta not in enviadas:

        cargo = o.get("desccargo", "Sin cargo")
        escuela = o.get("descestablecimiento", "Sin escuela")

        nuevas.append((id_oferta, f"{cargo} - {escuela}"))

if nuevas:

    client = Client(
        os.environ["TWILIO_SID"],
        os.environ["TWILIO_TOKEN"]
    )

    mensaje = "📢 NUEVAS OFERTAS EN PERGAMINO\n\n"

    for n in nuevas:
        mensaje += f"• {n[1]}\n"

    client.messages.create(
        body=mensaje,
        from_=os.environ["TWILIO_FROM"],
        to=os.environ["TWILIO_TO"]
    )

    for n in nuevas:
        enviadas.append(n[0])

    with open("ofertas_enviadas.json", "w") as f:
        json.dump(enviadas, f)
