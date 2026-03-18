"""
Lincoln Institute Debug — inspecciona HTML real tras scroll
"""
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

START_URL = "https://www.lincolninst.edu/all-publications/"

def init_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=opts)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"})
    return driver

driver = init_driver()
driver.get(START_URL)

# Esperar más tiempo para que cargue el JS
print("Esperando 8 segundos para que cargue el JS...")
time.sleep(8)

# Scroll una vez
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(4)

soup = BeautifulSoup(driver.page_source, "html.parser")

# 1) Todos los links NO de navegación
print("\n── TODOS LOS LINKS (filtrando navegación) ──")
skip = ["#", "facebook", "twitter", "linkedin", "instagram", "mailto",
        "/about", "/courses", "/data", "/endowment", "/for-media",
        "/centers", "/our-work", "/events", "es/", "pt-br/"]
count = 0
for a in soup.find_all("a", href=True):
    href  = a["href"]
    texto = a.get_text(strip=True)[:60]
    if not any(s in href for s in skip) and href not in ("/", ""):
        print(f"  href={href!r:80s}  texto={texto!r}")
        count += 1
        if count >= 80:
            print("  ... (mostrando primeros 80)")
            break

# 2) Buscar cualquier elemento que parezca una tarjeta de publicación
print("\n── ELEMENTOS CON CLASE QUE CONTIENE 'card', 'result', 'item', 'publication' ──")
for tag in soup.find_all(class_=True):
    classes = " ".join(tag.get("class", []))
    if any(kw in classes.lower() for kw in ["card", "result", "item", "publication", "post"]):
        print(f"  <{tag.name} class='{classes[:80]}'> → {tag.get_text(strip=True)[:60]}")
        break  # solo el primero para ver la estructura

# 3) Ver si hay iframes o elementos que cargan contenido externo
print("\n── IFRAMES / SCRIPTS EXTERNOS ──")
for iframe in soup.find_all("iframe"):
    print(f"  iframe src={iframe.get('src', '')!r}")
for script in soup.find_all("script", src=True):
    src = script.get("src", "")
    if "lincolninst" not in src and len(src) > 10:
        print(f"  script src={src!r}")

# 4) Guardar HTML completo para inspección
with open("lincoln_page.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)
print("\n── HTML guardado en lincoln_page.html ──")

driver.quit()