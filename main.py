import os
from playwright.sync_api import sync_playwright
from twilio.rest import Client

# distritos a buscar
DISTRITOS = ["PERGAMINO", "SALTO", "ROJAS"]

# archivo donde se guardan cargos ya avisados
ARCHIVO_CARGOS = "cargos_encontrados.txt"


def enviar_whatsapp(mensaje):

    sid = os.getenv("TWILIO_SID")
    token = os.getenv("TWILIO_TOKEN")
    from_number = os.getenv("TWILIO_FROM")
    to_number = os.getenv("TWILIO_TO")

    client = Client(sid, token)

    client.messages.create(
        from_=from_number,
        body=mensaje,
        to=to_number
    )


def cargar_cargos_guardados():

    if not os.path.exists(ARCHIVO_CARGOS):
        return set()

    with open(ARCHIVO_CARGOS, "r") as f:
        return set(f.read().splitlines())


def guardar_cargo(cargo):

    with open(ARCHIVO_CARGOS, "a") as f:
        f.write(cargo + "\n")


def revisar():

    usuario = os.getenv("ABC_USER")
    password = os.getenv("ABC_PASS")

    cargos_guardados = cargar_cargos_guardados()

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # LOGIN ABC
        page.goto("https://login.abc.gob.ar/nidp/idff/sso?id=ABC-Form&sid=0&option=credential&sid=0&target=https://menu.abc.gob.ar/")

        page.fill('input[name="username"]', usuario)
        page.fill('input[name="password"]', password)

        page.click('button[type="submit"]')

        page.wait_for_timeout(6000)

        # ACTOS PUBLICOS
        page.goto("https://misservicios.abc.gob.ar/actos.publicos.digitales/")

        page.wait_for_timeout(6000)

        contenido = page.content().upper()

        nuevos_cargos = []

        for distrito in DISTRITOS:

            if distrito in contenido:

                if distrito not in cargos_guardados:
                    nuevos_cargos.append(distrito)
                    guardar_cargo(distrito)

        if nuevos_cargos:

            mensaje = "Actos públicos encontrados:\n"

            for c in nuevos_cargos:
                mensaje += f"- {c}\n"

            enviar_whatsapp(mensaje)

        browser.close()


revisar()
