"""
Madeira DRE Debug 2 — inspecciona una página de detalle (InformacaoId)
para ver cómo están los PDFs dentro de cada ítem
"""
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Tomamos 3 ejemplos de distintas secciones del debug anterior
DETAIL_PAGES = [
    ("Ofício Circular",  "https://www.madeira.gov.pt/dre/Estrutura/DRE/Of%C3%ADcios-Circulares/ctl/Read/mid/16671/InformacaoId/252780/UnidadeOrganicaId/32/CatalogoId/0"),
    ("Publicação",       "https://www.madeira.gov.pt/dre/Estrutura/DRE/Publica%C3%A7%C3%B5es/ctl/Read/mid/6358/InformacaoId/251916/UnidadeOrganicaId/32/CatalogoId/0"),
    ("Legislação",       "https://www.madeira.gov.pt/dre/Estrutura/DRE/Legisla%C3%A7%C3%A3o/ctl/Read/mid/6349/InformacaoId/151140/UnidadeOrganicaId/32/CatalogoId/0"),
]

# También verificar si el listado tiene paginación
LISTING_PAGES = [
    ("Ofícios Circulares listado", "https://www.madeira.gov.pt/dre/Estrutura/DRE/Of%C3%ADcios-Circulares"),
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

# 1) Inspeccionar páginas de detalle
for name, url in DETAIL_PAGES:
    print(f"\n{'='*60}")
    print(f"DETALLE: {name}")
    print(f"URL: {url}")
    print('='*60)
    driver.get(url)
    time.sleep(4)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Todos los links
    print("── TODOS LOS LINKS ──")
    for a in soup.find_all("a", href=True):
        href  = a["href"]
        texto = a.get_text(strip=True)[:80]
        skip  = ["facebook","twitter","Login","javascript","sre","dre/Estrutura/DRE/A-Dir",
                 "Desporto","Ensino","Recursos","Projetos","Formação","Educação de"]
        if not any(s in href for s in skip) and href not in ("/",""):
            print(f"  href={href!r:90s}  texto={texto!r}")

    # PDFs
    pdfs = [a for a in soup.find_all("a", href=True) if ".pdf" in a["href"].lower()]
    print(f"\n── PDFs: {len(pdfs)} ──")
    for a in pdfs:
        print(f"  PDF: {a['href']!r}  →  {a.get_text(strip=True)[:60]!r}")

# 2) Ver paginación en listado
print(f"\n{'='*60}")
print("PAGINACIÓN EN LISTADO")
print('='*60)
driver.get(LISTING_PAGES[0][1])
time.sleep(4)
soup = BeautifulSoup(driver.page_source, "html.parser")
# Buscar elementos de paginación
for sel in [".pagination", ".pager", "[class*='page']", "li.next", "a[href*='page']"]:
    found = soup.select(sel)
    if found:
        print(f"  selector {sel!r}: {[str(x)[:150] for x in found[:3]]}")

# Contar ítems en el listado
items = [a for a in soup.find_all("a", href=True) if "InformacaoId" in a["href"]]
print(f"\n  Ítems con InformacaoId en página 1: {len(items)}")
print(f"  Último ítem: {items[-1]['href'] if items else 'ninguno'}")

driver.quit()
print("\nDone.")