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
MAX_PAGINAS = 50  # seguridad para no bucles infinitos

# --- SSL/TLS Adapter para Requests ---
class TLSAdapter(HTTPAdapter):
    """Forzar TLS 1.2+"""
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

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
def consultar_api(pagina, session):
    url = "https://misservicios.abc.gob.ar/actos.publicos.digitales/api/busqueda"
    payload = {"page": pagina, "estado": "PUBLICADA"}
    try:
        r = session.post(url, json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"❌ Error al consultar API: {e}")
        return {"data": []}

# --- Función principal de revisión ---
def revisar():
    historial = cargar_historial()
    encontrados = dict(historial)  # copia para actualizar
    nuevos = []

    # --- Session con TLS y headers ---
    session = requests.Session()
    session.mount("https://", TLSAdapter())
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    })

    pagina = 1
    while pagina <= MAX_PAGINAS:
        data = consultar_api(pagina, session)
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
    revisar()
