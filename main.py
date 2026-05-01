import requests
import time
import os
import re
import json
import random
from flask import Flask
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ARQUIVO_CACHE = "enviados.json"

LOJAS_CONFIAVEIS = [
    "amazon",
    "magalu",
    "magazine luiza",
    "casas bahia",
    "mercado livre",
    "fast shop",
    "pontofrio"
]

# 🔔 envio com log
def enviar(msg):
    print("📨 Tentando enviar mensagem...")
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("✅ Status envio:", r.status_code)
        print("📄 Resposta:", r.text)
    except Exception as e:
        print("❌ Erro ao enviar:", e)

# 🔒 cache
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

# 🌐 fetch paralelo
def fetch(url):
    try:
        print(f"🔎 Buscando: {url}")
        return requests.get(url, timeout=8).text
    except Exception as e:
        print("❌ Erro ao buscar:", e)
        return ""

def buscar_fontes():
    urls = [
        "https://api.allorigins.win/raw?url=https://www.promobit.com.br/busca/lg%20oled/",
        "https://api.allorigins.win/raw?url=https://www.pelando.com.br/search?q=lg%20oled"
    ]

    with ThreadPoolExecutor(max_workers=4) as executor:
        return list(executor.map(fetch, urls))

def identificar_loja(texto):
    texto = texto.lower()
    for loja in LOJAS_CONFIAVEIS:
        if loja in texto:
            return loja.title()
    return None

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
        r'<a.*?href="(.*?)".*?>(.*?)</a>.*?(?:R\$|\$)\s?(\d{1,3}(?:[\.,]\d{3})*)',
        html,
        re.IGNORECASE | re.DOTALL
    )

    print(f"🔍 Ofertas encontradas: {len(blocos)}")

    for link, titulo, preco in blocos:
        titulo_limpo = re.sub('<.*?>', '', titulo).strip().lower()

        if "lg" in titulo_limpo and "oled" in titulo_limpo:

            if any(x in titulo_limpo for x in ["usado", "open box", "reembalado"]):
                continue

            modelo_match = re.search(r'\b([cbg]\d)\b', titulo_limpo)
            modelo = modelo_match.group(1).upper() if modelo_match else "N/A"

            preco_int = int(preco.replace(".", "").replace(",", ""))

            loja = identificar_loja(titulo_limpo)
            if not loja:
                continue

            ofertas.append({
                "titulo": titulo_limpo.title(),
                "modelo": modelo,
                "preco": preco_int,
                "link": "https://www.promobit.com.br" + link if link.startswith("/") else link,
                "loja": loja
            })

    print(f"✅ Ofertas filtradas LG OLED: {len(ofertas)}")
    return ofertas

# 🧠 score inteligente
def score_oferta(preco, ref, titulo):
    desconto = (1 - preco / ref)
    score = 0

    if desconto > 0.5:
        score += 60
    elif desconto > 0.35:
        score += 40
    elif desconto > 0.2:
        score += 20

    if any(x in titulo for x in ["erro", "bug", "cupom"]):
        score += 20

    if preco < ref * 0.6:
        score += 30

    return score, int(desconto * 100)

def analisar():
    global enviados

    print("🔁 Rodando análise...")

    htmls = buscar_fontes()

    for html in htmls:
        if not html:
            continue

        ofertas = extrair_ofertas(html)

        for oferta in ofertas:
            link = oferta["link"]

            if link in enviados:
                continue

            preco = oferta["preco"]
            ref = get_preco_referencia(oferta["modelo"])

            score, desconto = score_oferta(preco, ref, oferta["titulo"])

            print(f"📊 {oferta['modelo']} - R${preco} - Score {score}")

            if score >= 70:
                nivel = "🔥 BUG ALTAMENTE PROVÁVEL"
            elif score >= 50:
                nivel = "⚡ POSSÍVEL BUG"
            elif score >= 30:
                nivel = "💰 BOA OPORTUNIDADE"
            else:
                continue

            enviar(f"""
{nivel}

📺 {oferta['titulo']}
🔎 Modelo: {oferta['modelo']}
🏪 Loja: {oferta['loja']}

💰 R$ {preco}
📊 Ref: R$ {ref}
📉 Desconto: {desconto}%
🧠 Score: {score}

🔗 {link}
""")

            enviados.add(link)
            salvar_enviados(enviados)

@app.route("/")
def home():
    return "Bot rodando!"

if __name__ == "__main__":
    print("🚀 BOT INICIANDO...")
    print("TOKEN:", "OK" if TOKEN else "FALTANDO")
    print("CHAT_ID:", "OK" if CHAT_ID else "FALTANDO")

    enviar("🤖 CAÇADOR INTELIGENTE ATIVO!")

    import threading

    def loop():
        while True:
            analisar()
            time.sleep(random.randint(30, 60))

    t = threading.Thread(target=loop)
    t.start()

    app.run(host="0.0.0.0", port=10000)
