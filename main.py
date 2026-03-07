import json
import subprocess
import os
from twilio.rest import Client

URL = "https://servicios3.abc.gob.ar/valoracion.docente/api/apd.oferta.encabezado/select?q=*:*&rows=10&sort=finoferta%20desc&fq=descdistrito:pergamino&wt=json"

print("Consultando actos públicos...")

result = subprocess.run(
    ["curl", "-s", URL],
    stdout=subprocess.PIPE
)

data = json.loads(result.stdout.decode("utf-8", errors="ignore"))

docs = data["response"]["docs"]

mensaje = "📢 Actos públicos en Pergamino\n\n"

for d in docs:

    id_oferta = d.get("idoferta")

    if not id_oferta:
        continue

    # endpoint detalle
    url_detalle = f"https://servicios3.abc.gob.ar/valoracion.docente/api/apd.oferta.detalle/select?q=idoferta:{id_oferta}&wt=json"

    detalle = subprocess.run(
        ["curl", "-s", url_detalle],
        stdout=subprocess.PIPE
    )

    data_det = json.loads(detalle.stdout.decode("utf-8", errors="ignore"))

    detalles = data_det["response"]["docs"]

    for det in detalles:

        materia = det.get("descmateria", "Sin materia")
        escuela = det.get("descestablecimiento", "Sin escuela")
        sigla = det.get("sigla", "")
        horas = det.get("horas", "")

        mensaje += f"""
📚 {materia}
🏫 {escuela}
🔹 {sigla}
⏱ {horas} horas

"""

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
