import streamlit as st
import httpx
import re
import asyncio
import trafilatura
import whois
import dns.resolver
import phonenumbers
import socket
from phonenumbers import carrier, geocoder
from duckduckgo_search import DDGS
from PIL import Image
from PIL.ExifTags import TAGS
from PicImageSearch import Yandex, Network

# --- НАСТРОЙКА ИНТЕРФЕЙСА ---
st.set_page_config(page_title="Mega OSINT Tool", page_icon="🕵️", layout="wide")
st.title("🕵️ Mega OSINT Tool")
st.markdown("Максимальный набор инструментов для сбора информации из открытых источников.")

# Создаем 7 вкладок
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "👤 Никнейм", "📱 Телефон", "📧 Email", "🌐 IP / Домен", 
    "🖼 Фото", "🖥 MAC-адрес", "🛠 Генератор Dorks"
])

# --- БАЗА САЙТОВ (40+ платформ) ---
SITES = {
    "GitHub": "https://github.com/{}", "VK": "https://vk.com/{}",
    "Instagram": "https://www.instagram.com/{}/", "TikTok": "https://www.tiktok.com/@{}",
    "Twitter (X)": "https://x.com/{}", "Reddit": "https://www.reddit.com/user/{}",
    "Steam": "https://steamcommunity.com/id/{}", "Pinterest": "https://www.pinterest.com/{}/",
    "Twitch": "https://www.twitch.tv/{}", "YouTube": "https://www.youtube.com/@{}",
    "Habr": "https://habr.com/ru/users/{}/", "Pikabu": "https://pikabu.ru/@{}",
    "Flickr": "https://www.flickr.com/people/{}", "SoundCloud": "https://soundcloud.com/{}",
    "Vimeo": "https://vimeo.com/{}", "Dribbble": "https://dribbble.com/{}",
    "Behance": "https://www.behance.net/{}", "Medium": "https://medium.com/@{}",
    "DeviantArt": "https://www.deviantart.com/{}", "Codeforces": "https://codeforces.com/profile/{}",
    "LeetCode": "https://leetcode.com/{}", "Telegram": "https://t.me/{}",
    "Figma": "https://www.figma.com/@{}", "Kaggle": "https://www.kaggle.com/{}",
    "AboutMe": "https://about.me/{}", "Keybase": "https://keybase.io/{}",
    "Mastodon": "https://mastodon.social/@{}", "GitLab": "https://gitlab.com/{}",
    "BitBucket": "https://bitbucket.org/{}/", "HackerNews": "https://news.ycombinator.com/user?id={}",
    "LiveJournal": "https://{}.livejournal.com", "Replit": "https://replit.com/@{}",
    "Scribd": "https://www.scribd.com/{}", "SlideShare": "https://www.slideshare.net/{}",
    "Trello": "https://trello.com/{}", "ProductHunt": "https://www.producthunt.com/@{}",
    "Giphy": "https://giphy.com/{}", "Wattpad": "https://www.wattpad.com/user/{}"
}

async def check_site(client, name, url_template, user):
    url = url_template.format(user)
    try:
        resp = await client.get(url, timeout=5.0, follow_redirects=True)
        if resp.status_code == 200:
            page_text = resp.text.lower()
            negative_markers = ["page not found", "user not found", "couldn't find", "не найдена", "не найден", "doesn't exist", "no user"]
            if not any(marker in page_text for marker in negative_markers):
                return f"✅ [{name}]({url})"
    except Exception:
        pass
    return None

def scan_ports(ip):
    common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 3389, 8080]
    open_ports = []
    for port in common_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((ip, port))
        if result == 0:
            open_ports.append(port)
        sock.close()
    return open_ports

# ==========================================
# ВКЛАДКА 1: НИК
# ==========================================
with tab1:
    st.header("Поиск по никнейму (40+ платформ)")
    user_in = st.text_input("Введите ник (без @):", key="u_in")
    if st.button("Сканировать профили", key="b_u"):
        if user_in:
            with st.spinner(f"Сканирую {len(SITES)} сайтов..."):
                async def run_scan():
                    async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
                        tasks = [check_site(client, n, u, user_in) for n, u in SITES.items()]
                        return [r for r in await asyncio.gather(*tasks) if r]
                res = asyncio.run(run_scan())
                if res:
                    st.success(f"Найдено профилей: {len(res)}")
                    for r in res: st.markdown(r)
                else:
                    st.warning("Не найдено.")
            
            st.subheader("🕵️ Упоминания и сливы:")
            with DDGS() as ddgs:
                for q in [f'"{user_in}" (email OR почта)', f'"{user_in}" (утечка OR слив)']:
                    for r in list(ddgs.text(q, max_results=2)):
                        st.markdown(f"- [{r['title'][:50]}...]({r['href']})")

# ==========================================
# ВКЛАДКА 2: ТЕЛЕФОН
# ==========================================
with tab2:
    st.header("Анализ телефона")
    phone_in = st.text_input("Номер (+7...):", key="p_in")
    if st.button("Анализировать", key="b_p"):
        if phone_in:
            try:
                num = phonenumbers.parse(phone_in, "RU")
                if phonenumbers.is_valid_number(num):
                    st.success(f"Оператор: {carrier.name_for_number(num, 'ru')} | Регион: {geocoder.description_for_number(num, 'ru')}")
                digits = re.sub(r'\D', '', phone_in)
                if len(digits) == 11 and digits.startswith('8'): digits = '7' + digits[1:]
                st.markdown(f"[WhatsApp](https://wa.me/{digits}) | [Telegram](https://t.me/+{digits}) | [Truecaller](https://www.truecaller.com/search/ru/{digits})")
                
                with DDGS() as ddgs:
                    st.subheader("Упоминания:")
                    for r in list(ddgs.text(f'"{digits}" (site:vk.com OR site:avito.ru OR база)', max_results=4)):
                        st.markdown(f"- [{r['title']}]({r['href']})")
            except Exception as e: st.error(f"Ошибка: {e}")

# ==========================================
# ВКЛАДКА 3: EMAIL
# ==========================================
with tab3:
    st.header("Анализ Email")
    email_in = st.text_input("Email:", key="e_in")
    if st.button("Искать Email", key="b_e"):
        if email_in:
            st.subheader("Поиск в утечках и на форумах:")
            with DDGS() as ddgs:
                for q in [f'"{email_in}" (утечка OR слив OR database)', f'"{email_in}" site:pastebin.com']:
                    for r in list(ddgs.text(q, max_results=3)):
                        st.markdown(f"- [{r['title'][:60]}...]({r['href']})")

# ==========================================
# ВКЛАДКА 4: IP / ДОМЕН
# ==========================================
with tab4:
    st.header("IP и Домены")
    target_in = st.text_input("Введите IP или домен:", key="ip_in")
    if st.button("Проверить", key="b_ip"):
        if target_in:
            if re.fullmatch(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', target_in):
                with st.spinner("Геолокация и сканирование портов..."):
                    try:
                        data = httpx.get(f"http://ip-api.com/json/{target_in}?lang=ru").json()
                        if data.get('status') == 'success':
                            st.info(f"Страна: {data['country']}, Город: {data['city']}, ISP: {data['isp']}")
                        
                        st.subheader("🔓 Открытые порты:")
                        ports = scan_ports(target_in)
                        if ports: st.success(f"Найдены порты: {', '.join(map(str, ports))}")
                        else: st.warning("Популярные порты закрыты.")
                    except Exception as e: st.error(f"Ошибка: {e}")
            
            elif '.' in target_in:
                with st.spinner("Сбор DNS и WHOIS..."):
                    try:
                        answers = dns.resolver.resolve(target_in, 'A')
                        st.info(f"A-запись: {', '.join([r.address for r in answers])}")
                    except: pass
                    
                    try:
                        st.subheader("Поддомены (crt.sh):")
                        crt_resp = httpx.get(f"https://crt.sh/?q=%.{target_in}&output=json", timeout=10)
                        if crt_resp.status_code == 200:
                            subdomains = set(item['name_value'] for item in crt_resp.json())
                            for sub in list(subdomains)[:10]:
                                st.markdown(f"- {sub}")
                    except: st.warning("Не удалось получить поддомены.")
                    
                    try:
                        w = whois.whois(target_in)
                        st.info(f"Создан: {w.creation_date}")
                    except: pass

# ==========================================
# ВКЛАДКА 5: ФОТО
# ==========================================
with tab5:
    st.header("Фото: EXIF и Поиск")
    file = st.file_uploader("Фото", type=["jpg", "png"])
    if file:
        img = Image.open(file)
        st.image(img, width=250)
        if st.button("Анализ", key="b_ph"):
            with st.spinner("Ищу..."):
                ex = img.getexif()
                for k, v in ex.items():
                    if TAGS.get(k) in ["Make", "Model", "DateTime"]: st.write(f"{TAGS.get(k)}: {v}")
                
                async def y_search():
                    async with Network() as c:
                        return await Yandex(client=c).search(file=file.getvalue())
                try:
                    res = asyncio.run(y_search())
                    if res.raw:
                        for i in res.raw[:3]: st.markdown(f"[{i.title}]({i.url})")
                except Exception as e: st.error(f"Ошибка Яндекс: {e}")

# ==========================================
# ВКЛАДКА 6: MAC-АДРЕС
# ==========================================
with tab6:
    st.header("MAC-адрес (Производитель)")
    mac_in = st.text_input("Введите MAC (например, 00:1A:2B:3C:4D:5E):", key="m_in")
    if st.button("Определить", key="b_m"):
        if mac_in:
            try:
                resp = httpx.get(f"https://api.macvendors.com/{mac_in}")
                if resp.status_code == 200:
                    st.success(f"Производитель: {resp.text}")
                else:
                    st.warning("Производитель не найден.")
            except Exception as e: st.error(f"Ошибка: {e}")

# ==========================================
# ВКЛАДКА 7: DORKS ГЕНЕРАТОР
# ==========================================
with tab7:
    st.header("Генератор Google Dorks")
    st.write("Эти запросы помогут найти уязвимости или скрытые файлы на сайтах.")
    domain_in = st.text_input("Введите домен (например, site.com):", key="d_in")
    if st.button("Сгенерировать", key="b_d"):
        if domain_in:
            dorks = [
                f"site:{domain_in} ext:sql", f"site:{domain_in} ext:env",
                f"site:{domain_in} intitle:\"index of\"", f"site:{domain_in} inurl:admin",
                f"site:{domain_in} inurl:login", f"site:{domain_in} ext:log",
                f"site:{domain_in} ext:bak", f"site:{domain_in} \"password\"",
                f"site:{domain_in} \"api_key\""
            ]
            for d in dorks:
                st.code(d)
