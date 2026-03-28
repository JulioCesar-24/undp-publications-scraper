"""
Madeira DRE — PDF Scraper
=========================
Sitio: https://www.madeira.gov.pt/dre

Estrategia:
  1. Cargar cada sección con Selenium (JS necesario)
  2. Recoger todos los links /ctl/Read/.../InformacaoId/XXXXX/...
  3. Visitar cada ítem y extraer PDFs de //Portals/15/documentos/

Requisitos:
    pip install selenium webdriver-manager pandas beautifulsoup4

Uso:
    python madeira_pdf_scraper.py

Salida:
    madeira_pdfs.csv
"""

import time
import pandas as pd
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
BASE_URL    = "https://www.madeira.gov.pt"
OUTPUT_FILE = "madeira_pdfs.csv"
DELAY       = 2.0   # entre páginas de listado
DET_DELAY   = 1.5   # entre páginas de detalle

# Todas las secciones del sitio con sus URLs
SECTIONS = [
    # DRE principal
    ("DRE / Instrumentos de Gestão",        "/dre/Estrutura/DRE/A-Dire%C3%A7%C3%A3o/Instrumentos-de-Gest%C3%A3o"),
    ("DRE / Recursos Humanos",              "/dre/Estrutura/DRE/A-Dire%C3%A7%C3%A3o/Recursos-Humanos"),
    ("DRE / Ofícios Circulares",            "/dre/Estrutura/DRE/Of%C3%ADcios-Circulares"),
    ("DRE / Publicações",                   "/dre/Estrutura/DRE/Publica%C3%A7%C3%B5es"),
    ("DRE / Legislação",                    "/dre/Estrutura/DRE/Legisla%C3%A7%C3%A3o"),
    ("DRE / Protocolos",                    "/dre/Estrutura/DRE/Protocolos"),
    ("DRE / Estratégia Cidadania",          "/dre/Estrutura/DRE/Estrat%C3%A9gia-Regional-de-Educa%C3%A7%C3%A3o-para-a-Cidadania"),
    # Áreas
    ("Áreas / Educação e Ensino",           "/dre/Estrutura/DRE/Areas/Educa%C3%A7%C3%A3o-e-Ensino"),
    ("Áreas / Educação Pré-Escolar",        "/dre/Estrutura/DRE/Areas/Educa%C3%A7%C3%A3o-e-Ensino/Educa%C3%A7%C3%A3o-de-Inf%C3%A2ncia-e-Educa%C3%A7%C3%A3o-Pr%C3%A9-Escolar"),
    ("Áreas / Ensino Básico",               "/dre/Estrutura/DRE/Areas/Educa%C3%A7%C3%A3o-e-Ensino/Ensino-B%C3%A1sico"),
    ("Áreas / Ensino Secundário",           "/dre/Estrutura/DRE/Areas/Educa%C3%A7%C3%A3o-e-Ensino/Ensino-Secund%C3%A1rio"),
    ("Áreas / Educação de Adultos",         "/dre/Estrutura/DRE/Areas/Educa%C3%A7%C3%A3o-e-Ensino/Educa%C3%A7%C3%A3o-de-Adultos"),
    ("Áreas / Recursos Especializados",     "/dre/Estrutura/DRE/Areas/Recursos-Especializados-Especializados"),
    ("Áreas / Tecnologias de Apoio",        "/dre/Estrutura/DRE/Areas/Recursos-Especializados-Especializados/Tecnologias-de-Apoio"),
    ("Áreas / Surdez e Cegueira",           "/dre/Estrutura/DRE/Areas/Recursos-Especializados-Especializados/Surdez-e-Cegueira"),
    ("Áreas / Centros Recursos Educativos", "/dre/Estrutura/DRE/Areas/Recursos-Especializados-Especializados/Centros-de-Recursos-Educativos"),
    ("Áreas / Educação Especial",           "/dre/Estrutura/DRE/Areas/Recursos-Especializados-Especializados/Servi%C3%A7os-T%C3%A9cnicos/Educa%C3%A7%C3%A3o-Especial"),
    ("Áreas / Formação Profissional",       "/dre/Estrutura/DRE/Areas/Recursos-Especializados-Especializados/Servi%C3%A7os-T%C3%A9cnicos/Forma%C3%A7%C3%A3o-Profissional"),
    ("Áreas / Educação Artística",          "/dre/Estrutura/DRE/Areas/Educa%C3%A7%C3%A3o-Art%C3%ADstica"),
    ("Áreas / Desporto Escolar",            "/dre/Estrutura/DRE/Areas/Desporto-Escolar"),
    ("Áreas / Desporto Documentos",         "/dre/Estrutura/DRE/Areas/Desporto-Escolar/Documentos"),
    ("Áreas / Formação Inovação",           "/dre/Estrutura/DRE/Areas/Forma%C3%A7%C3%A3o-Inova%C3%A7%C3%A3o"),
    ("Áreas / Edu-LE Documentos",           "/dre/Estrutura/DRE/Areas/Forma%C3%A7%C3%A3o-Inova%C3%A7%C3%A3o/Edu-LE/Documentos"),
    ("Áreas / Projetos Europeus",           "/dre/Estrutura/DRE/ProjetosEuropeus"),
]

# ─────────────────────────────────────────────
# NAVEGADOR
# ─────────────────────────────────────────────

def init_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=opts)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
    )
    return driver


def get_soup(driver, url, wait_seconds=None):
    driver.get(url)
    if wait_seconds:
        time.sleep(wait_seconds)
    else:
        time.sleep(DELAY)
    return BeautifulSoup(driver.page_source, "html.parser")


# ─────────────────────────────────────────────
# FASE 1 — Recolectar URLs de ítems por sección
# ─────────────────────────────────────────────

def collect_item_urls(driver):
    """Recorre cada sección y recoge todos los links InformacaoId únicos."""
    all_items = []   # lista de (category, item_url)
    seen      = set()

    print("=" * 60)
    print("FASE 1: Recolectando ítems por sección…")
    print("=" * 60)

    for category, path in SECTIONS:
        url  = urljoin(BASE_URL, path)
        print(f"\n  [{category}]")
        print(f"  {url}")

        soup = get_soup(driver, url, wait_seconds=3)

        count = 0
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "InformacaoId" in href:
                full = href if href.startswith("http") else urljoin(BASE_URL, href)
                full = full.replace("http://", "https://")
                if full not in seen:
                    seen.add(full)
                    all_items.append((category, full, a.get_text(strip=True)))
                    count += 1

        print(f"  → {count} ítems nuevos  (total acumulado: {len(all_items)})")

    print(f"\n  ✅ Total ítems: {len(all_items)}\n")
    return all_items


# ─────────────────────────────────────────────
# FASE 2 — Visitar cada ítem y extraer PDFs
# ─────────────────────────────────────────────

def collect_pdfs(driver, items):
    all_pdfs = []
    total    = len(items)

    print("=" * 60)
    print("FASE 2: Buscando PDFs en cada ítem…")
    print("=" * 60)

    for i, (category, url, listing_title) in enumerate(items, 1):
        print(f"  [{i}/{total}] {listing_title[:60]}")
        soup = get_soup(driver, url, wait_seconds=DET_DELAY)

        # Título: h1 o h2 de la página de detalle
        h1    = soup.find("h1") or soup.find("h2")
        title = h1.get_text(strip=True) if h1 else listing_title

        # Buscar PDFs: //Portals/15/... o cualquier .pdf
        pdfs_found    = []
        seen_pdf_urls = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if ".pdf" in href.lower():
                # Normalizar URL
                full = href if href.startswith("http") else urljoin(BASE_URL, href)
                full = full.replace("http://", "https://").replace("//Portals", "/Portals")
                if full not in seen_pdf_urls:
                    seen_pdf_urls.add(full)
                    pdf_title = a.get_text(strip=True) or title
                    pdfs_found.append((pdf_title, full))

        if pdfs_found:
            for pdf_title, pdf_url in pdfs_found:
                all_pdfs.append({
                    "category":        category,
                    "item_title":      title,
                    "pdf_title":       pdf_title,
                    "pdf_url":         pdf_url,
                    "item_url":        url,
                })
            print(f"    ✅ {len(pdfs_found)} PDF(s)")
        else:
            print(f"    ⚠️  Sin PDF")
            all_pdfs.append({
                "category":    category,
                "item_title":  title,
                "pdf_title":   "",
                "pdf_url":     "",
                "item_url":    url,
            })

    return all_pdfs


# ─────────────────────────────────────────────
# GUARDAR CSV
# ─────────────────────────────────────────────

def save_csv(data):
    df      = pd.DataFrame(data)
    df_pdfs = df[df["pdf_url"] != ""].drop_duplicates(subset=["pdf_url"])
    df_all  = df.drop_duplicates(subset=["item_url"])
    df_pdfs.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n✅ Guardado: {OUTPUT_FILE}")
    print(f"   Ítems procesados:       {len(df_all)}")
    print(f"   PDFs únicos:            {len(df_pdfs)}")
    print(f"   Ítems sin PDF:          {len(df_all) - len(df[df['pdf_url'] != ''].drop_duplicates(subset=['item_url']))}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🔍 Madeira DRE — PDF Scraper")
    print(f"Sitio: {BASE_URL}/dre\n")

    driver = init_driver()
    try:
        items = collect_item_urls(driver)
        if items:
            pdfs = collect_pdfs(driver, items)
            save_csv(pdfs)
        else:
            print("\n[AVISO] No se encontraron ítems.")
    finally:
        driver.quit()
        print("\nNavegador cerrado.")