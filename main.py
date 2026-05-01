import requests
import time
import os
import re
from flask import Flask

app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# memória simples pra evitar repetição
enviados = set()

def enviar(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def buscar_html():
    url = "https://api.allorigins.win/raw?url=https://www.promobit.com.br/busca/lg%20oled/"
    try:
        return requests.get(url, timeout=10).text
    except:
        return ""

def get_preco_referencia(modelo):
    referencias = {
        "C3": 5500,
        "C2": 5000,
        "B2": 4800
    }
    return referencias.get(modelo, 4800)

def extrair_ofertas(html):
    ofertas = []

    blocos = re.findall(
        r'<a.*?href="(.*?)".*?>(.*?)</a>.*?r\$\s?(\d{1,3}(?:\.\d{3})*)',
        html,
        re.IGNORECASE | re.DOTALL
    )

    for link, titulo, preco in blocos:
        titulo_limpo = re.sub('<.*?>', '', titulo).strip()

        if "lg" in titulo_limpo.lower() and "oled" in titulo_limpo.lower():

            modelo_match = re.search(r'\b([cbg]\d)\b', titulo_limpo.lower())
            modelo = modelo_match.group(1).upper() if modelo_match else "N/A"

            preco_int = int(preco.replace(".", ""))

            ofertas.append({
                "titulo": titulo_limpo,
                "modelo": modelo,
                "preco": preco_int,
                "link": "https://www.promobit.com.br" + link if link.startswith("/") else link
            })

    return ofertas

def analisar():
    html = buscar_html()
    if not html:
        return

    ofertas = extrair_ofertas(html)

    for oferta in ofertas:
        modelo = oferta["modelo"]
        preco = oferta["preco"]
        ref = get_preco_referencia(modelo)

        desconto = int((1 - preco / ref) * 100)

        # evita repetição (usa link como ID)
        if oferta["link"] in enviados:
            continue

        # filtro profissional
        if preco < ref * 0.9:  # pelo menos 10% abaixo

            # classificação
            if desconto >= 50:
                nivel = "🔥 BUG FORTE"
            elif desconto >= 35:
                nivel = "⚡ OFERTA INSANA"
            elif desconto >= 20:
                nivel = "💰 ÓTIMA OFERTA"
            else:
                nivel = "📉 abaixo do normal"

            enviar(f"""
{nivel}

📺 {oferta['titulo']}
🔎 Modelo: {modelo}
💰 R$ {preco}
📊 Referência: R$ {ref}
📉 Desconto: {desconto}%

🔗 {oferta['link']}
""")

            enviados.add(oferta["link"])

@app.route("/")
def home():
    return "Bot rodando!"

if __name__ == "__main__":
    enviar("🤖 CAÇADOR LG OLED ATIVO!")

    import threading

    def loop():
        while True:
            analisar()
            time.sleep(300)

    t = threading.Thread(target=loop)
    t.start()

    app.run(host="0.0.0.0", port=10000)
