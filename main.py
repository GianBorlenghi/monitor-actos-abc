import os
from playwright.sync_api import sync_playwright
from twilio.rest import Client

DISTRITOS = ["PERGAMINO", "SALTO", "ROJAS"]
ARCHIVO_CARGOS = "historial.txt"


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


def guardar_historial(lista):

    with open(ARCHIVO_CARGOS, "a") as f:
        for item in lista:
            f.write(item + "\n")


def filtrar_estado(page):

    page.click('button[data-target=".autocomplete-estado-modal"]')

    page.wait_for_selector("#autocompleteEstadoQuery")

    page.fill("#autocompleteEstadoQuery", "PUBLICADA")

    page.keyboard.press("Enter")

    page.wait_for_timeout(2000)


def filtrar_distrito(page, distrito):

    page.click('button[data-target=".autocomplete-distrito-modal"]')

    page.wait_for_selector("#autocompleteDistritoQuery")

    page.fill("#autocompleteDistritoQuery", distrito)

    page.keyboard.press("Enter")

    page.wait_for_timeout(4000)


def leer_tabla(page):

    page.wait_for_selector("table tbody tr")

    filas = page.query_selector_all("table tbody tr")

    resultados = []

    for fila in filas:

        columnas = fila.query_selector_all("td")

        if len(columnas) < 5:
            continue

        distrito = columnas[0].inner_text().strip().upper()
        escuela = columnas[1].inner_text().strip()
        cargo = columnas[2].inner_text().strip()
        cierre = columnas[4].inner_text().strip()

        resultados.append({
            "distrito": distrito,
            "escuela": escuela,
            "cargo": cargo,
            "cierre": cierre
        })

    return resultados


def revisar():

    historial = cargar_historial()

    nuevos = []
    encontrados = []

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Entrando a ABC...")

        page.goto("https://misservicios.abc.gob.ar/actos.publicos.digitales/")

        page.wait_for_timeout(6000)

        # cerrar popup si aparece
        if page.locator(".modal.show").count() > 0:
            page.keyboard.press("Escape")

        page.wait_for_timeout(2000)

        # aplicar filtro estado una sola vez
        filtrar_estado(page)

        for distrito in DISTRITOS:

            print("Buscando en:", distrito)

            filtrar_distrito(page, distrito)

            resultados = leer_tabla(page)

            for r in resultados:

                identificador = f"{r['distrito']}-{r['escuela']}-{r['cargo']}-{r['cierre']}"

                encontrados.append(identificador)

                if identificador not in historial:

                    nuevos.append(r)

        if nuevos:

            mensaje = "📢 NUEVOS ACTOS PUBLICOS ABC\n\n"

            for c in nuevos:

                mensaje += (
                    f"🏫 {c['escuela']}\n"
                    f"📍 {c['distrito']}\n"
                    f"📚 {c['cargo']}\n"
                    f"⏰ {c['cierre']}\n\n"
                )

            enviar_whatsapp(mensaje)

            guardar_historial(encontrados)

            print("WhatsApp enviado")

        else:
            print("Sin cargos nuevos")

        browser.close()


revisar()
