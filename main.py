import os
from playwright.sync_api import sync_playwright
from twilio.rest import Client

DISTRITOS = ["PERGAMINO", "SALTO", "ROJAS"]

def enviar_whatsapp(mensaje):

    sid = os.getenv("TWILIO_SID")
    token = os.getenv("TWILIO_TOKEN")

    client = Client(sid, token)

    client.messages.create(
        from_='whatsapp:+14155238886',
        body=mensaje,
        to='whatsapp:+549TU_NUMERO'
    )

def revisar():

    usuario = os.getenv("ABC_USER")
    password = os.getenv("ABC_PASS")

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("URL_LOGIN_ABC")

        page.fill('input[name="username"]', usuario)
        page.fill('input[name="password"]', password)

        page.click('button[type="submit"]')

        page.wait_for_timeout(5000)

        page.goto("URL_ACTOS_PUBLICOS")

        contenido = page.content().upper()

        for d in DISTRITOS:
            if d in contenido:
                enviar_whatsapp(f"Nuevo cargo encontrado en {d}")

        browser.close()

revisar()
