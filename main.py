import json
import subprocess
import os
from twilio.rest import Client

URL = "https://servicios3.abc.gob.ar/valoracion.docente/api/apd.oferta.encabezado/select?q=*:*&rows=20&sort=finoferta%20desc&fq=descdistrito:pergamino&wt=json"

print("Consultando actos públicos...")

# usamos curl porque requests falla con SSL en este servidor
result = subprocess.run(
    ["curl", "-s", URL],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)

docs = data["response"]["docs"]

if not docs:
    print("No hay resultados")
    exit()

mensaje = "📢 Actos públicos en Pergamino\n\n"

for d in docs:
    cargo = d.get("desccargo", "Sin cargo")
    institucion = d.get("desctipoinstitucion", "")
    fecha_fin = d.get("finoferta", "")

    mensaje += f"• {cargo}\n{institucion}\nFin: {fecha_fin}\n\n"

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

print("Mensaje enviado correctamente")
