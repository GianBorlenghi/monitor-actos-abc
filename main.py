import json
import subprocess
import os
from datetime import datetime
from twilio.rest import Client

URL = "https://servicios3.abc.gob.ar/valoracion.docente/api/apd.oferta.encabezado/select?q=*:*&rows=100&sort=finoferta%20desc&fq=descdistrito:pergamino&fq=estado:publicada&wt=json"

# -----------------------------
# CONTROL DE HORARIO
# -----------------------------

ahora = datetime.now()

hora = ahora.hour
dia_semana = ahora.weekday()  # 0 lunes - 6 domingo

# no correr sábado ni domingo
if dia_semana >= 5:
    print("Fin de semana, no se ejecuta")
    exit()

# horario permitido 10:00 a 23:59
if hora < 10 or hora >= 24:
    print("Fuera de horario")
    exit()

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

# -----------------------------
# CARGOS YA ENVIADOS
# -----------------------------

archivo_cache = "enviados.json"

if os.path.exists(archivo_cache):
    with open(archivo_cache) as f:
        enviados = json.load(f)
else:
    enviados = []

lineas = []
nuevos_ids = []

for d in docs:

    idoferta = str(d.get("id", ""))

    if idoferta in enviados:
        continue

    cargo = d.get("descripcioncargo", "Sin cargo")
    escuela = d.get("escuela", "Sin escuela")
    curso = d.get("cursodivision", "")

    linea = f"""
📚 {cargo}
🏫 {escuela}
👨‍🎓 {curso}
"""

    lineas.append(linea)
    nuevos_ids.append(idoferta)

if len(lineas) == 0:
    print("No hay cargos nuevos")
    exit()

# -----------------------------
# MENSAJES
# -----------------------------

mensajes = []
actual = "📢 Nuevos actos públicos en Pergamino\n"

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

# -----------------------------
# GUARDAR ENVIADOS
# -----------------------------

enviados.extend(nuevos_ids)

with open(archivo_cache, "w") as f:
    json.dump(enviados, f)
