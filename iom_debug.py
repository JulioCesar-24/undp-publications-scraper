"""
IOM Debug 2 — muestra TODOS los links de la página, no solo los primeros 50
"""
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

START_URL = "https://publications.iom.int/search"
BASE_URL  = "https://publications.iom.int"

def init_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=opts)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"})
    return driver

driver = init_driver()
driver.get(START_URL)
time.sleep(4)
soup = BeautifulSoup(driver.page_source, "html.parser")

# Mostrar TODOS los links (no solo 50)
print("── TODOS LOS LINKS DE LA PÁGINA ──")
for a in soup.find_all("a", href=True):
    href = a["href"]
    texto = a.get_text(strip=True)[:60]
    # Ignorar links de navegación/filtros que ya conocemos
    skip = ["#", "facebook", "twitter", "mailto", "iom.int/", "/user", "/about", "/contact",
            "/my-reading", "eepurl", "search?f%", "/es/", "/fr/", "Back to", "Skip to",
            "Log in", "Subscribe", "English", "Español", "FRANÇAIS"]
    if not any(s in href or s in texto for s in skip):
        print(f"  href={href!r:70s}  texto={texto!r}")

driver.quit()