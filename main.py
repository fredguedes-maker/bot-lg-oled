import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def enviar(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def verificar():
    produtos = [
        {
            "nome": "LG OLED 55 C3",
            "preco": 2499,
            "preco_medio": 5500,
            "link": "https://exemplo.com"
        }
    ]

    for p in produtos:
        if "LG" in p["nome"] and "OLED" in p["nome"]:
            if p["preco"] < 0.6 * p["preco_medio"]:
                enviar(f"""
🚨 POSSÍVEL BUG DETECTADO

📺 {p["nome"]}
💰 R$ {p["preco"]}
📉 Normal: ~R$ {p["preco_medio"]}

🔗 {p["link"]}
""")

# mensagem inicial (pra teste)
enviar("🤖 Bot iniciado com sucesso!")

while True:
    verificar()
    time.sleep(300)
