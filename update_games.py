import requests
from bs4 import BeautifulSoup
import json
import os

# ==========================================
# 0. CONFIGURAÇÃO DO TELEGRAM
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

def enviar_alerta_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return # Se não tiver as chaves configuradas, não tenta enviar

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar para o Telegram: {e}")

def enviar_alerta_discord(mensagem):
    if not DISCORD_WEBHOOK_URL:
        return
    payload = {"content": mensagem}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Erro ao enviar para o Discord: {e}")

# ==========================================
# 1. LENDO JOGOS ANTIGOS (Para não notificar repetido)
# ==========================================
jogos_conhecidos = set()
if os.path.exists("games.json"):
    try:
        with open("games.json", "r", encoding="utf-8") as f:
            dados_antigos = json.load(f)
            for jogo in dados_antigos.get("promotions_now", []):
                jogos_conhecidos.add(jogo["url"])
    except Exception:
        pass # Se o arquivo não existir ou estiver corrompido, segue o jogo

games_now = []
games_next = []

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
}

# ==========================================
# 2. EPIC GAMES
# ==========================================
print("Buscando jogos da Epic Games...")
url_epic = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions?locale=pt-BR&country=BR&allowCountries=BR"

try:
    data_epic = requests.get(url_epic, headers=headers).json()
    elements = data_epic.get("data", {}).get("Catalog", {}).get("searchStore", {}).get("elements", [])
    
    for game in elements:
        slug = None
        
        mappings = game.get("catalogNs", {}).get("mappings")
        if mappings and len(mappings) > 0:
            slug = mappings[0].get("pageSlug")
            
        if not slug:
            offer_mappings = game.get("offerMappings")
            if offer_mappings and len(offer_mappings) > 0:
                slug = offer_mappings[0].get("pageSlug")
                
        if not slug or slug == "[]":
            slug = game.get("productSlug")
            
        if not slug or slug == "[]":
            slug = game.get("urlSlug")
            
        if not slug:
            continue

        game_url = f"https://store.epicgames.com/en-US/p/{slug}"

        image = None
        for img in game.get("keyImages", []):
            if img["type"] in ["OfferImageWide", "DieselStoreFrontWide"]:
                image = img["url"]
                break

        if not image and game.get("keyImages"):
            image = game["keyImages"][0]["url"]

        price_info = game.get("price", {}).get("totalPrice", {})
        original_price = price_info.get("fmtPrice", {}).get("originalPrice", "0")
        discount_price_formatted = price_info.get("fmtPrice", {}).get("discountPrice", "0")
        
        raw_discount_price = price_info.get("discountPrice", -1)
        if raw_discount_price != 0:
            continue

        promotions = game.get("promotions")
        if not promotions:
            continue

        offers = promotions.get("promotionalOffers")
        if offers:
            for offer in offers:
                for promo in offer.get("promotionalOffers", []):
                    games_now.append({
                        "title": game.get("title", "Mystery Game"),
                        "image": image,
                        "url": game_url,
                        "end": promo.get("endDate"),
                        "original_price": original_price,
                        "discount_price": discount_price_formatted,
                        "store": "Epic"
                    })

        upcoming = promotions.get("upcomingPromotionalOffers")
        if upcoming:
            for offer in upcoming:
                for promo in offer.get("promotionalOffers", []):
                    games_next.append({
                        "title": game.get("title", "Mystery Game"),
                        "image": image,
                        "url": game_url,
                        "start": promo.get("startDate"),
                        "original_price": original_price,
                        "discount_price": discount_price_formatted,
                        "store": "Epic"
                    })
                    
except Exception as e:
    print(f"Erro ao buscar na Epic: {e}")

# ==========================================
# 3. STEAM
# ==========================================
print("Buscando jogos da Steam...")
url_steam = "https://store.steampowered.com/search/?sort_by=Price_ASC&ignore_preferences=1&maxprice=free&specials=1&ndl=1"

try:
    response_steam = requests.get(url_steam, headers=headers)
    response_steam.raise_for_status()
    soup = BeautifulSoup(response_steam.text, 'html.parser')
    
    resultados = soup.find_all('a', class_='search_result_row')
    for item in resultados:
        title_elem = item.find('span', class_='title')
        title = title_elem.text.strip() if title_elem else "Jogo da Steam"
        
        game_url = item.get('href', '').split('?')[0]
        app_id = item.get('data-ds-appid')
        if not app_id: continue
            
        image_url = ""
        capsule_div = item.find('div', class_='search_capsule')
        if capsule_div:
            img_tag = capsule_div.find('img')
            if img_tag and img_tag.get('src'):
                image_url = img_tag.get('src').split('?')[0]
        
        original_price_elem = item.find('div', class_='discount_original_price')
        original_price = original_price_elem.text.strip() if original_price_elem else "Pago"
        
        games_now.append({
            "title": title,
            "image": image_url,
            "url": game_url,
            "end": None,
            "original_price": original_price,
            "discount_price": "0",
            "is_free": True,
            "store": "Steam"
        })
except Exception as e:
    print(f"Erro ao buscar na Steam: {e}")

# ==========================================
# 4. VERIFICANDO NOVIDADES E NOTIFICANDO
# ==========================================
novos_jogos = []
for jogo in games_now:
    if jogo["url"] not in jogos_conhecidos:
        novos_jogos.append(jogo)

if novos_jogos:
    print(f"Encontrei {len(novos_jogos)} jogos novos! Enviando notificação para o Telegram...")
    for novo_jogo in novos_jogos:
        msg = f"*{novo_jogo['title']}*\n"
        msg += f"{novo_jogo['url']}"
        enviar_alerta_telegram(msg)
        enviar_alerta_discord(msg)
else:
    print("Nenhum jogo novo encontrado desta vez.")

# ==========================================
# 5. INDIEGALA
# ==========================================
print("Buscando jogos da IndieGala...")
url_indiegala = "https://freebies.indiegala.com/"

try:
    response_indiegala = requests.get(url_indiegala, headers=headers)
    response_indiegala.raise_for_status()
    soup_ig = BeautifulSoup(response_indiegala.text, 'html.parser')
    
    # Buscando os blocos internos de produto conforme o HTML fornecido
    resultados_ig = soup_ig.find_all('div', class_='products-col-inner')
    
    for item in resultados_ig:
        # Pega a URL do jogo
        link_tag = item.find('a', class_='fit-click')
        game_url = link_tag.get('href') if link_tag else None
        
        # Pega o Título
        title_elem = item.find('div', class_='product-title')
        title = title_elem.text.strip() if title_elem else "IndieGala Freebie"
        
        # Pega a URL da imagem (Lazy load data-img-src)
        img_tag = item.find('img', class_='async-img-load')
        image_url = img_tag.get('data-img-src') if img_tag else ""
        
        if game_url:
            games_now.append({
                "title": title,
                "image": image_url,
                "url": game_url,
                "end": None,
                "original_price": "Pago", # IndieGala freebies não mostram o preço original de forma simples
                "discount_price": "0",
                "is_free": True,
                "store": "IndieGala"
            })
            
except Exception as e:
    print(f"Erro ao buscar na IndieGala: {e}")

# ==========================================
# 6. SALVANDO O ARQUIVO FINAL
# ==========================================
games_now.sort(key=lambda x: x["url"])
games_next.sort(key=lambda x: x["url"])

output = {
    "promotions_now": games_now,
    "next_week": games_next
}

conteudo_mudou = True

# Se o arquivo já existir, vamos ler e comparar logicamente com os dados novos
if os.path.exists("games.json"):
    try:
        with open("games.json", "r", encoding="utf-8") as f:
            dados_antigos = json.load(f)
            if dados_antigos == output:
                conteudo_mudou = False
    except Exception:
        pass

# Só sobrescreve o arquivo se algo realmente mudou (jogo novo ou jogo que expirou)
if conteudo_mudou:
    with open("games.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"Concluído! Modificações detectadas. games.json atualizado com {len(games_now)} jogos.")
else:
    print("Concluído! Nenhuma alteração nos jogos. O arquivo games.json foi mantido intacto.")
