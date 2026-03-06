import os
from playwright.sync_api import sync_playwright
from twilio.rest import Client

DISTRITOS = ["PERGAMINO", "SALTO", "ROJAS"]
ARCHIVO_CARGOS = "cargos_guardados.txt"


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


def cargar_historial():

    if not os.path.exists(ARCHIVO_CARGOS):
        return set()

    with open(ARCHIVO_CARGOS, "r") as f:
        return set(f.read().splitlines())


def guardar_historial(cargo):

    with open(ARCHIVO_CARGOS, "a") as f:
        f.write(cargo + "\n")


def revisar():

    usuario = os.getenv("ABC_USER")
    password = os.getenv("ABC_PASS")

    historial = cargar_historial()

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # LOGIN
        page.goto("https://login.abc.gob.ar/nidp/idff/sso?id=ABC-Form&sid=0&option=credential&sid=0&target=https://menu.abc.gob.ar/")

        page.wait_for_selector("#Ecom_User_ID")

        page.fill("#Ecom_User_ID", usuario)
        page.fill("#Ecom_Password", password)

        page.click('a:has-text("ENTRAR")')

        page.wait_for_timeout(7000)

        # ACTOS PUBLICOS
        page.goto("https://misservicios.abc.gob.ar/actos.publicos.digitales/")

        page.wait_for_timeout(8000)

        # FILTRO ESTADO PUBLICADA
        page.click('button[data-target=".autocomplete-estado-modal"]')

        page.wait_for_selector("#autocompleteEstadoQuery")

        page.fill("#autocompleteEstadoQuery", "PUBLICADA")

        page.keyboard.press("Enter")

        page.wait_for_timeout(4000)

        # TABLA
        page.wait_for_selector("table tbody tr")

        filas = page.query_selector_all("table tbody tr")

        nuevos_cargos = []

        for fila in filas:

            columnas = fila.query_selector_all("td")

            if len(columnas) < 5:
                continue

            distrito = columnas[0].inner_text().strip().upper()
            escuela = columnas[1].inner_text().strip()
            cargo = columnas[2].inner_text().strip()
            cierre = columnas[4].inner_text().strip()

            if distrito in DISTRITOS:

                identificador = f"{distrito}-{escuela}-{cargo}-{cierre}"

                if identificador not in historial:

                    nuevos_cargos.append({
                        "distrito": distrito,
                        "escuela": escuela,
                        "cargo": cargo,
                        "cierre": cierre
                    })

                    guardar_historial(identificador)

        if nuevos_cargos:

            mensaje = "📢 NUEVOS ACTOS PUBLICOS\n\n"

            for c in nuevos_cargos:

                mensaje += (
                    f"🏫 Escuela: {c['escuela']}\n"
                    f"📍 Distrito: {c['distrito']}\n"
                    f"📚 Cargo: {c['cargo']}\n"
                    f"⏰ Cierre: {c['cierre']}\n\n"
                )

            enviar_whatsapp(mensaje)

        browser.close()


revisar()
