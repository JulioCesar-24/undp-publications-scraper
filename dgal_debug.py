"""
Portal Autárquico DGAL — Debug
Inspecciona la página de destaques y una subsección con PDFs
"""
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

PAGES = [
    ("Destaques",              "https://portalautarquico.dgal.gov.pt/pt-PT/destaques/"),
    ("Finanças / Publicações", "https://portalautarquico.dgal.gov.pt/pt-PT/financas-locais/publicacoes-e-estudos"),
    ("Assuntos Jurídicos",     "https://portalautarquico.dgal.gov.pt/pt-PT/assuntos-juridicos/pareceres-e-outros"),
]

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
    return driver

driver = init_driver()

NAV_SKIP = ["facebook", "linkedin", "SISAL", "reservado", "Contactos", "FAQS",
            "subsetor-da-administracao", "financas-locais", "transferencia-de-competencias",
            "cooperacao-tecnica", "assuntos-juridicos", "direcao-geral", "javascript", "#"]

for name, url in PAGES:
    print(f"\n{'='*60}")
    print(f"PÁGINA: {name}")
    print(f"URL: {url}")
    print('='*60)

    driver.get(url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Links no-nav
    print("\n── LINKS (primeros 40, sin nav) ──")
    count = 0
    for a in soup.find_all("a", href=True):
        href  = a["href"]
        texto = a.get_text(strip=True)[:70]
        if not any(s in href for s in NAV_SKIP) and href not in ("/", ""):
            print(f"  href={href!r:90s}  texto={texto!r}")
            count += 1
            if count >= 40:
                print("  ...")
                break

    # PDFs directos
    pdfs = [a for a in soup.find_all("a", href=True) if ".pdf" in a["href"].lower()]
    print(f"\n── PDFs DIRECTOS: {len(pdfs)} ──")
    for a in pdfs[:10]:
        print(f"  {a['href']!r}  →  {a.get_text(strip=True)[:60]!r}")

    # Paginación
    print(f"\n── PAGINACIÓN ──")
    for sel in [".pagination", ".pager", "[class*='page']", "a[href*='page']", "a[href*='PageIndex']"]:
        found = soup.select(sel)
        if found:
            print(f"  {sel}: {[str(x)[:120] for x in found[:2]]}")

driver.quit()
print("\nDone.")