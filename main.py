'''import httpx
import json
from twilio.rest import Client
import os

# --- CONFIGURACIÓN ---
DISTRITOS = ["PERGAMINO", "ROJAS", "SALTO"]
HISTORIAL_FILE = "historial.json"
MAX_PAGINAS = 50  # límite de seguridad para no bucles infinitos

# --- Funciones de historial ---
def cargar_historial():
    if not os.path.exists(HISTORIAL_FILE):
        return {}
    with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
        return {item["id"]: item["fechaCierre"] for item in json.load(f)}

def guardar_historial(historial_dict):
    data = [{"id": k, "fechaCierre": v} for k, v in historial_dict.items()]
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Función para enviar WhatsApp ---
def enviar_whatsapp(msg):
    sid = os.environ.get("TWILIO_SID")
    auth = os.environ.get("TWILIO_AUTH")
    from_whatsapp = os.environ.get("TWILIO_FROM")
    to_whatsapp = os.environ.get("TWILIO_TO")

    if not all([sid, auth, from_whatsapp, to_whatsapp]):
        print("⚠️ Variables de entorno de Twilio no configuradas")
        return

    client = Client(sid, auth)
    client.messages.create(
        body=msg,
        from_=from_whatsapp,
        to=to_whatsapp
    )

# --- Función para consultar la API ---
def consultar_api(pagina, client):
    url = "https://misservicios.abc.gob.ar/actos.publicos.digitales/api/busqueda"
    payload = {"page": pagina, "estado": "PUBLICADA"}
    try:
        r = client.post(url, json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except httpx.RequestError as e:
        print(f"❌ Error al consultar API: {e}")
        return {"data": []}

# --- Función principal de revisión ---
def revisar():
    historial = cargar_historial()
    encontrados = dict(historial)  # copia para actualizar
    nuevos = []

    # --- Cliente HTTPX con headers tipo navegador ---
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }

    with httpx.Client(timeout=15, headers=headers, verify=True) as client:
        pagina = 1
        while pagina <= MAX_PAGINAS:
            data = consultar_api(pagina, client)
            resultados = data.get("data", [])

            if not resultados:
                break

            for r in resultados:
                distrito = r.get("distrito", "").upper()
                if distrito not in DISTRITOS:
                    continue

                identificador = str(r.get("id"))
                fechaCierre = r.get("fechaCierre", "")

                encontrados[identificador] = fechaCierre

                if identificador not in historial:
                    nuevos.append(r)

            pagina += 1

    # --- Enviar WhatsApp si hay nuevos cargos ---
    if nuevos:
        msg = "📢 ACTOS PÚBLICOS NUEVOS\n\n"
        for n in nuevos:
            msg += (
                f"🏫 {n.get('establecimiento','-')}\n"
                f"📍 {n.get('distrito','-')}\n"
                f"📚 {n.get('cargo','-')}\n"
                f"⏰ {n.get('fechaCierre','-')}\n\n"
            )
        enviar_whatsapp(msg)
        print(f"✅ WhatsApp enviado con {len(nuevos)} cargos nuevos")
    else:
        print("ℹ️ Sin novedades")

    guardar_historial(encontrados)

# --- Ejecutar ---
if __name__ == "__main__":
    revisar()'''

import requests
import json
from twilio.rest import Client
import os
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

# --- CONFIGURACIÓN ---
DISTRITOS = ["PERGAMINO", "ROJAS", "SALTO"]
HISTORIAL_FILE = "historial.json"
MAX_PAGINAS = 50


# --- Adapter SSL compatible ---
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")  # permite ciphers viejos del servidor
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ctx
        )


# --- sesión HTTP ---
session = requests.Session()
session.mount("https://", TLSAdapter())

session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json"
})


# --- HISTORIAL ---
def cargar_historial():
    if not os.path.exists(HISTORIAL_FILE):
        return {}

    with open(HISTORIAL_FILE, "r") as f:
        data = json.load(f)

    return {item["id"]: item["fechaCierre"] for item in data}


def guardar_historial(historial):
    data = [{"id": k, "fechaCierre": v} for k, v in historial.items()]

    with open(HISTORIAL_FILE, "w") as f:
        json.dump(data, f, indent=2)


# --- WHATSAPP ---
def enviar_whatsapp(msg):

    sid = os.environ.get("TWILIO_SID")
    auth = os.environ.get("TWILIO_AUTH")
    from_whatsapp = os.environ.get("TWILIO_FROM")
    to_whatsapp = os.environ.get("TWILIO_TO")

    if not sid:
        print("⚠️ Twilio no configurado")
        return

    client = Client(sid, auth)

    client.messages.create(
        body=msg,
        from_=from_whatsapp,
        to=to_whatsapp
    )


# --- CONSULTAR API ---
def consultar_api(pagina):

    url = "https://misservicios.abc.gob.ar/actos.publicos.digitales/api/busqueda"

    payload = {
        "page": pagina,
        "estado": "PUBLICADA"
    }

    try:

        r = session.post(url, json=payload, timeout=20)

        if r.status_code != 200:
            print("⚠️ status:", r.status_code)
            return {"data": []}

        return r.json()

    except Exception as e:

        print("❌ Error al consultar API:", e)
        return {"data": []}


# --- BOT PRINCIPAL ---
def revisar():

    historial = cargar_historial()
    encontrados = dict(historial)

    nuevos = []

    pagina = 1

    while pagina <= MAX_PAGINAS:

        data = consultar_api(pagina)

        resultados = data.get("data", [])

        if not resultados:
            break

        for r in resultados:

            distrito = r.get("distrito", "").upper()

            if distrito not in DISTRITOS:
                continue

            id_acto = str(r.get("id"))
            fecha = r.get("fechaCierre")

            encontrados[id_acto] = fecha

            if id_acto not in historial:
                nuevos.append(r)

        pagina += 1

    if nuevos:

        msg = "📢 ACTOS PUBLICOS NUEVOS\n\n"

        for n in nuevos:

            msg += (
                f"🏫 {n.get('establecimiento')}\n"
                f"📍 {n.get('distrito')}\n"
                f"📚 {n.get('cargo')}\n"
                f"⏰ {n.get('fechaCierre')}\n\n"
            )

        enviar_whatsapp(msg)

        print("✅ WhatsApp enviado:", len(nuevos))

    else:

        print("ℹ️ Sin novedades")

    guardar_historial(encontrados)


if __name__ == "__main__":
    revisar()
