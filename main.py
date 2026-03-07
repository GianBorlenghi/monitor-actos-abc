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

texto = result.stdout.decode("utf-8", errors="ignore")

if not texto.strip():
    print("La API no devolvió datos")
    exit()

data = json.loads(texto)

docs = data.get("response", {}).get("docs", [])

if len(docs) == 0:
    print("No hay cargos")
    exit()

mensaje = "📢 Actos públicos en Pergamino\n\n"

for d in docs:

    cargo = d.get("descripcioncargo", "Sin cargo")
    escuela = d.get("escuela", "Sin escuela")
    direccion = d.get("domiciliodesempeno", "")
    curso = d.get("cursodivision", "")
    fin = d.get("finoferta", "")

    mensaje += f"""
📚 {cargo}
🏫 Escuela: {escuela}
📍 {direccion}
👨‍🎓 Curso: {curso}
⏰ Cierra: {fin}

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
