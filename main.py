import json
import subprocess
import os
from twilio.rest import Client

URL = "https://servicios3.abc.gob.ar/valoracion.docente/api/apd.oferta.encabezado/select?q=*:*&rows=100&sort=finoferta%20desc&fq=descdistrito:pergamino&fq=estado:publicada&wt=json"

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

lineas = []

for d in docs:

    cargo = d.get("descripcioncargo", "Sin cargo")
    escuela = d.get("escuela", "Sin escuela")
    curso = d.get("cursodivision", "")
    fin = d.get("finoferta", "")

    linea = f"""
📚 {cargo}
🏫 {escuela}
👨‍🎓 {curso}
"""

    lineas.append(linea)

# armar mensajes de max 1500 caracteres
mensajes = []
actual = "📢 Actos públicos en Pergamino\n"

for l in lineas:

    if len(actual) + len(l) > 1500:
        mensajes.append(actual)
        actual = ""

    actual += l

if actual:
    mensajes.append(actual)

print(f"Se enviarán {len(mensajes)} mensajes")

client = Client(
    os.environ["TWILIO_SID"],
    os.environ["TWILIO_TOKEN"]
)

for m in mensajes:

    client.messages.create(
        body=m,
        from_=os.environ["TWILIO_FROM"],
        to=os.environ["TWILIO_TO"]
    )

print("Mensajes enviados")
