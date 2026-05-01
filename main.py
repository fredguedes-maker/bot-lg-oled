import requests
import time
import os
import re
import json
from flask import Flask

app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ARQUIVO_CACHE = "enviados.json"

def enviar(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# 🔒 salvar histórico
def carregar_enviados():
    try:
        with open(ARQUIVO_CACHE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def salvar_enviados(enviados):
    with open(ARQUIVO_CACHE, "w") as f:
        json.dump(list(enviados), f)

enviados = carregar_enviados()

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

def identificar_loja(texto):
    texto = texto.lower()
    if "amazon" in texto:
        return "Amazon"
    elif "magalu" in texto or "magazine luiza" in texto:
        return "Magalu"
    elif "casas bahia" in texto:
        return "Casas Bahia"
    elif "mercado livre" in texto:
        return "Mercado Livre"
    else:
        return "Loja não identificada"

def extrair_ofertas(html):
    ofertas = []

    blocos = re.findall(
        r'<a.*?href="(.*?)".*?>(.*?)</a>.*?(?:R\$|\$)\s?(\d{1,3}(?:\.\d{3})*)',
        html,
        re.IGNORECASE | re.DOTALL
    )

    for link, titulo, preco in blocos:
        titulo_limpo = re.sub('<.*?>', '', titulo).strip()

        if "lg" in titulo_limpo.lower() and "oled" in titulo_limpo.lower():

            # ignora usados / open box
            if any(x in titulo_limpo.lower() for x in ["usado", "open box", "reembalado"]):
                continue

            modelo_match = re.search(r'\b([cbg]\d)\b', titulo_limpo.lower())
            modelo = modelo_match.group(1).upper() if modelo_match else "N/A"

            preco_int = int(preco.replace(".", ""))

            loja = identificar_loja(titulo_limpo)

            ofertas.append({
                "titulo": titulo_limpo,
                "modelo": modelo,
                "preco": preco_int,
                "link": "https://www.promobit.com.br" + link if link.startswith("/") else link,
                "loja": loja
            })

    return ofertas

def classificar_oferta(preco, ref):
    desconto = int((1 - preco / ref) * 100)

    if desconto >= 50:
        return "🔥 BUG FORTE", desconto
    elif desconto >= 35:
        return "⚡ OFERTA INSANA", desconto
    elif desconto >= 20:
        return "💰 ÓTIMA OFERTA", desconto
    else:
        return "📉 abaixo do normal", desconto

def analisar():
    global enviados

    html = buscar_html()
    if not html:
        return

    ofertas = extrair_ofertas(html)

    for oferta in ofertas:
        link = oferta["link"]

        if link in enviados:
            continue

        modelo = oferta["modelo"]
        preco = oferta["preco"]
        ref = get_preco_referencia(modelo)

        # filtro profissional
        if preco < ref * 0.9:

            nivel, desconto = classificar_oferta(preco, ref)

            enviar(f"""
{nivel}

📺 {oferta['titulo']}
🔎 Modelo: {modelo}
🏪 Loja: {oferta['loja']}

💰 R$ {preco}
📊 Referência: R$ {ref}
📉 Desconto: {desconto}%

🔗 {link}
""")

            enviados.add(link)
            salvar_enviados(enviados)

@app.route("/")
def home():
    return "Bot rodando!"

if __name__ == "__main__":
    enviar("🤖 CAÇADOR LG OLED PRO+ ATIVO!")

    import threading

    def loop():
        while True:
            analisar()
            time.sleep(300)

    t = threading.Thread(target=loop)
    t.start()

    app.run(host="0.0.0.0", port=10000)
