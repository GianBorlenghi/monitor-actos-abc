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

r = requests.get(URL, params=params)
data = r.json()

ofertas = data["response"]["docs"]

# cargar ofertas enviadas
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

        texto = f"{cargo} - {escuela}"

        nuevas.append((id_oferta, texto))

if nuevas:

    account_sid = os.environ["TWILIO_SID"]
    auth_token = os.environ["TWILIO_TOKEN"]

    client = Client(account_sid, auth_token)

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
