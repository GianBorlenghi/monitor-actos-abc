import json
import subprocess
import os
from twilio.rest import Client

URL = "https://servicios3.abc.gob.ar/valoracion.docente/api/apd.oferta.encabezado/select?q=*:*&rows=20&sort=finoferta%20desc&fq=descdistrito:pergamino&wt=json"

print("Consultando actos públicos...")

result = subprocess.run(
    ["curl", "-s", URL],
    stdout=subprocess.PIPE
)

# decodificar ignorando caracteres raros
data_text = result.stdout.decode("utf-8", errors="ignore")

data = json.loads(data_text)

docs = data["response"]["docs"]

if not docs:
    print("No hay actos")
    exit()

mensaje = "📢 Actos públicos en Pergamino\n\n"

for d in docs:

    cargo = d.get("desccargo", "Sin cargo")
    escuela = d.get("desctipoinstitucion", "")
    fin = d.get("finoferta", "")

    mensaje += f"• {cargo}\n{escuela}\nFin: {fin}\n\n"

print("Enviando WhatsApp...")

client = Client(
    os.environ["TWILIO_SID"],
    os.environ["TWILIO_TOKEN"]
)

client.messages.create(
    body=mensaje,
    from_=os.environ["TWILIO_FROM"],
    to=os.environ["TWILIO_TO"]
)

print("Mensaje enviado")
