import requests
import json
from twilio.rest import Client
import os

# distritos a buscar
DISTRITOS = ["PERGAMINO", "ROJAS", "SALTO"]

# tu whatsapp (callmebot)
PHONE = os.environ.get("PHONE")
APIKEY = os.environ.get("APIKEY")

HISTORIAL = "historial.json"


def cargar_historial():

    if not os.path.exists(HISTORIAL):
        return []

    with open(HISTORIAL) as f:
        return json.load(f)


def guardar_historial(data):

    with open(HISTORIAL, "w") as f:
        json.dump(data, f)


def enviar_whatsapp(msg):

    sid = os.environ.get("TWILIO_SID")
    auth = os.environ.get("TWILIO_TOKEN")
    from_whatsapp = os.environ.get("TWILIO_FROM")
    to_whatsapp = os.environ.get("TWILIO_TO")

    client = Client(sid, auth)

    client.messages.create(
        body=msg,
        from_=from_whatsapp,
        to=to_whatsapp
    )

def consultar_api(pagina):

    url = "https://misservicios.abc.gob.ar/actos.publicos.digitales/api/busqueda"

    payload = {
        "page": pagina,
        "estado": "PUBLICADA"
    }

    r = requests.post(url, json=payload)

    return r.json()


def revisar():

    historial = cargar_historial()

    nuevos = []
    encontrados = []

    pagina = 1

    while True:

        data = consultar_api(pagina)

        resultados = data["data"]

        if not resultados:
            break

        for r in resultados:

            distrito = r["distrito"]

            if distrito not in DISTRITOS:
                continue

            identificador = f"{r['id']}"

            encontrados.append(identificador)

            if identificador not in historial:

                nuevos.append(r)

        pagina += 1

    if nuevos:

        msg = "📢 ACTOS PUBLICOS\n\n"

        for n in nuevos:

            msg += (
                f"🏫 {n['establecimiento']}\n"
                f"📍 {n['distrito']}\n"
                f"📚 {n['cargo']}\n"
                f"⏰ {n['fechaCierre']}\n\n"
            )

        enviar_whatsapp(msg)

        print("WhatsApp enviado")

    else:
        print("Sin novedades")

    guardar_historial(encontrados)


if __name__ == "__main__":
    revisar()
