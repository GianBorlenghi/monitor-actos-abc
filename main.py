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

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os
from twilio.rest import Client

USUARIO = os.environ["ABC_USER"]
PASSWORD = os.environ["ABC_PASS"]

TWILIO_SID = os.environ["TWILIO_SID"]
TWILIO_AUTH = os.environ["TWILIO_AUTH"]
TWILIO_FROM = os.environ["TWILIO_FROM"]
TWILIO_TO = os.environ["TWILIO_TO"]

def enviar_whatsapp(msg):
    client = Client(TWILIO_SID, TWILIO_AUTH)
    client.messages.create(
        body=msg,
        from_=TWILIO_FROM,
        to=TWILIO_TO
    )

def buscar_actos():

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)

    try:

        driver.get("https://misservicios.abc.gob.ar")

        time.sleep(3)

        driver.find_element(By.NAME, "Ecom_User_ID").send_keys(USUARIO)
        driver.find_element(By.NAME, "Ecom_Password").send_keys(PASSWORD)

        driver.find_element(By.NAME, "login").click()

        time.sleep(5)

        driver.get("https://misservicios.abc.gob.ar/actos.publicos.digitales")

        time.sleep(5)

        html = driver.page_source

        if "cargo" in html.lower():
            enviar_whatsapp("⚠️ Hay nuevos actos públicos publicados")

            print("mensaje enviado")
        else:
            print("sin novedades")

    finally:
        driver.quit()


if __name__ == "__main__":
    buscar_actos()
