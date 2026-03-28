"""
Madeira DRE Debug — inspecciona HTML real tras carga JS
"""
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

PAGES = [
    ("Ofícios Circulares", "https://www.madeira.gov.pt/dre/Estrutura/DRE/Of%C3%ADcios-Circulares"),
    ("Publicações",        "https://www.madeira.gov.pt/dre/Estrutura/DRE/Publica%C3%A7%C3%B5es"),
    ("Legislação",         "https://www.madeira.gov.pt/dre/Estrutura/DRE/Legisla%C3%A7%C3%A3o"),
]

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
    return driver

driver = init_driver()

for name, url in PAGES:
    print(f"\n{'='*60}")
    print(f"SECCIÓN: {name}")
    print(f"URL: {url}")
    print('='*60)

    driver.get(url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Todos los links que NO sean de menú de navegación
    skip = ["#", "facebook", "twitter", "linkedin", "instagram", "mailto",
            "/sre", "Login", "javascript", "madeira.gov.pt/dre/Estrutura/DRE/Areas",
            "Desporto", "Formação", "Projetos", "Educação", "Ensino", "Recursos"]
    print(f"\n── LINKS (filtrando nav) ──")
    count = 0
    for a in soup.find_all("a", href=True):
        href  = a["href"]
        texto = a.get_text(strip=True)[:70]
        if not any(s in href for s in skip) and href not in ("/", ""):
            if "madeira.gov.pt" in href or href.startswith("/"):
                print(f"  href={href!r:80s}  texto={texto!r}")
                count += 1
                if count >= 30:
                    print("  ... (primeros 30)")
                    break

    # PDFs directos
    pdfs = [a for a in soup.find_all("a", href=True) if ".pdf" in a["href"].lower()]
    print(f"\n── PDFs ENCONTRADOS: {len(pdfs)} ──")
    for a in pdfs[:10]:
        print(f"  {a['href']!r}  →  {a.get_text(strip=True)[:60]!r}")

driver.quit()
print("\nDone.")