import os
import requests
from twilio.rest import Client

DISTRITOS = ["PERGAMINO", "SALTO", "ROJAS"]
ARCHIVO_CARGOS = "cargos_guardados.txt"

API_URL = "https://misservicios.abc.gob.ar/actos.publicos.digitales/api/ofertas"


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

    try:
        with open(ARCHIVO_CARGOS, "r") as f:
            return set(f.read().splitlines())
    except:
        return set()


def guardar_historial(cargo):

    with open(ARCHIVO_CARGOS, "a") as f:
        f.write(cargo + "\n")


def obtener_cargos():

    params = {
        "estado": "PUBLICADA",
        "page": 0,
        "size": 100
    }

    r = requests.get(API_URL, params=params)

    return r.json()


def revisar():

    historial = cargar_historial()

    datos = obtener_cargos()

    nuevos = []

    for oferta in datos["content"]:

        distrito = oferta["distrito"].upper()

        if distrito not in DISTRITOS:
            continue

        escuela = oferta["establecimiento"]
        cargo = oferta["cargo"]
        cierre = oferta["fechaCierre"]

        identificador = f"{distrito}-{escuela}-{cargo}-{cierre}"

        if identificador not in historial:

            nuevos.append({
                "distrito": distrito,
                "escuela": escuela,
                "cargo": cargo,
                "cierre": cierre
            })

            guardar_historial(identificador)

    if nuevos:

        mensaje = "📢 NUEVOS ACTOS PUBLICOS\n\n"

        for c in nuevos:

            mensaje += (
                f"🏫 Escuela: {c['escuela']}\n"
                f"📍 Distrito: {c['distrito']}\n"
                f"📚 Cargo: {c['cargo']}\n"
                f"⏰ Cierre: {c['cierre']}\n\n"
            )

        enviar_whatsapp(mensaje)


if __name__ == "__main__":
    revisar()
