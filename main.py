import requests
import time
import os
from flask import Flask

app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def enviar(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

@app.route("/")
def home():
    return "Bot rodando!"

def verificar():
    produtos = [
        {
            "nome": "LG OLED",
            "preco": 2499,
            "preco_medio": 5500,
            "link": "https://exemplo.com"
        }
    ]

    for p in produtos:
        if "LG" in p["nome"] and "OLED" in p["nome"]:
            if p["preco"] < 0.6 * p["preco_medio"]:
                enviar(f"🚨 BUG: {p['nome']} - R$ {p['preco']}")

if __name__ == "__main__":
    enviar("🤖 Bot iniciado!")

    import threading

    def loop():
        while True:
            verificar()
            time.sleep(300)

    t = threading.Thread(target=loop)
    t.start()

    app.run(host="0.0.0.0", port=10000)
