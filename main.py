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

texto = result.stdout.decode("utf-8", errors="ignore")

if not texto.strip():
    print("La API no devolvió datos")
    exit()

data = json.loads(texto)

docs = data.get("response", {}).get("docs", [])

mensaje = "📢 Actos públicos en Pergamino\n\n"

for d in docs:

    id_oferta = d.get("idoferta")

    if not id_oferta:
        continue

    url_detalle = f"https://servicios3.abc.gob.ar/valoracion.docente/api/apd.oferta.detalle/select?q=idoferta:{id_oferta}&wt=json"

    detalle = subprocess.run(
        ["curl", "-s", url_detalle],
        stdout=subprocess.PIPE
    )

    texto_det = detalle.stdout.decode("utf-8", errors="ignore")

    if not texto_det.strip():
        continue

    try:
        data_det = json.loads(texto_det)
    except:
        continue

    detalles = data_det.get("response", {}).get("docs", [])

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

if mensaje.strip() == "📢 Actos públicos en Pergamino":
    print("No hay cargos")
    exit()

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
