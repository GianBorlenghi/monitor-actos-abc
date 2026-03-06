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
import time
import json
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from twilio.rest import Client


DISTRITOS = ["PERGAMINO", "ROJAS", "SALTO"]

HISTORIAL_FILE = "historial.json"


def cargar_historial():

    if not os.path.exists(HISTORIAL_FILE):
        return []

    with open(HISTORIAL_FILE) as f:
        return json.load(f)


def guardar_historial(data):

    with open(HISTORIAL_FILE, "w") as f:
        json.dump(data, f)


def enviar_whatsapp(msg):

    sid = os.environ.get("TWILIO_SID")
    token = os.environ.get("TWILIO_TOKEN")
    from_whatsapp = os.environ.get("TWILIO_FROM")
    to_whatsapp = os.environ.get("TWILIO_TO")

    client = Client(sid, token)

    client.messages.create(
        body=msg,
        from_=from_whatsapp,
        to=to_whatsapp
    )


def iniciar_driver():

    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    return driver


def login(driver):

    print("Abriendo portal...")

    driver.get("https://misservicios.abc.gob.ar/actos.publicos.digitales/")

    wait = WebDriverWait(driver, 30)

    usuario = wait.until(
        EC.presence_of_element_located((By.NAME, "Ecom_User_ID"))
    )

    password = driver.find_element(By.NAME, "Ecom_Password")

    usuario.send_keys(os.environ.get("ABC_USER"))
    password.send_keys(os.environ.get("ABC_PASS"))

    password.send_keys(Keys.ENTER)

    time.sleep(8)


def aplicar_estado(driver):

    wait = WebDriverWait(driver, 30)

    print("Abriendo filtro estado")

    boton = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[data-target=".autocomplete-estado-modal"]')
        )
    )

    driver.execute_script("arguments[0].click();", boton)

    print("Esperando modal estado")

    estado = wait.until(
        EC.visibility_of_element_located((By.ID, "autocompleteEstadoQuery"))
    )

    estado.send_keys("PUBLICADA")

    time.sleep(2)

    estado.send_keys(Keys.ENTER)

    time.sleep(4)


def aplicar_distrito(driver, distrito):

    wait = WebDriverWait(driver, 20)

    print("Buscando distrito:", distrito)

    botones = driver.find_elements(By.CSS_SELECTOR, "button.btnFiltro")

    boton_distrito = botones[0]

    driver.execute_script("arguments[0].click();", boton_distrito)

    dist = wait.until(
        EC.visibility_of_element_located((By.ID, "autocompleteDistritoQuery"))
    )

    dist.clear()
    dist.send_keys(distrito)

    time.sleep(2)

    dist.send_keys(Keys.ENTER)

    time.sleep(5)


def leer_tabla(driver):

    filas = driver.find_elements(By.CSS_SELECTOR, "tbody tr")

    datos = []

    for f in filas:

        c = f.find_elements(By.TAG_NAME, "td")

        if len(c) < 6:
            continue

        establecimiento = c[1].text
        distrito = c[2].text.upper()
        cargo = c[3].text
        fecha = c[5].text

        datos.append({
            "establecimiento": establecimiento,
            "distrito": distrito,
            "cargo": cargo,
            "fecha": fecha
        })

    return datos


def buscar_actos():

    driver = iniciar_driver()

    login(driver)

    print("Entrando a actos públicos")

    driver.get(
        "https://misservicios.abc.gob.ar/actos.publicos.digitales/#/actosPublicos"
    )

    time.sleep(12)

    aplicar_estado(driver)

    historial = cargar_historial()

    encontrados = []
    nuevos = []

    for d in DISTRITOS:

        aplicar_distrito(driver, d)

        resultados = leer_tabla(driver)

        print("Filas encontradas:", len(resultados))

        for r in resultados:

            identificador = r["establecimiento"] + r["cargo"] + r["fecha"]

            encontrados.append(identificador)

            if identificador not in historial:

                nuevos.append(r)

    if nuevos:

        msg = "📢 ACTOS PUBLICOS NUEVOS\n\n"

        for n in nuevos:

            msg += (
                f"🏫 {n['establecimiento']}\n"
                f"📍 {n['distrito']}\n"
                f"📚 {n['cargo']}\n"
                f"⏰ {n['fecha']}\n\n"
            )

        enviar_whatsapp(msg)

        print("WhatsApp enviado")

    else:

        print("Sin novedades")

    guardar_historial(encontrados)

    driver.quit()


if __name__ == "__main__":
    buscar_actos()
