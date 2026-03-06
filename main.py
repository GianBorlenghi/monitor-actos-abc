
from playwright.sync_api import sync_playwright
from twilio.rest import Client

USUARIO = "TU_USUARIO"
PASSWORD = "TU_PASSWORD"

DISTRITOS = ["PERGAMINO", "SALTO", "ROJAS"]

def enviar_whatsapp(mensaje):

    account_sid = "TWILIO_SID"
    auth_token = "TWILIO_TOKEN"

    client = Client(account_sid, auth_token)

    client.messages.create(
        from_='whatsapp:+14155238886',
        body=mensaje,
        to='whatsapp:+549TU_NUMERO'
    )


def revisar():

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://abc.gob.ar")

        page.fill('input[name="username"]', USUARIO)
        page.fill('input[name="password"]', PASSWORD)

        page.click('button[type="submit"]')

        page.wait_for_timeout(5000)

        page.goto("URL_ACTOS_PUBLICOS")

        contenido = page.content()

        texto = contenido.upper()

        for d in DISTRITOS:
            if d in texto:
                enviar_whatsapp(f"Nuevo cargo en {d}")

        browser.close()


revisar()
