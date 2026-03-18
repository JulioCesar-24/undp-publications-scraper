"""
Lincoln Institute of Land Policy — PDF Scraper (corregido)
===========================================================
Sitio: https://www.lincolninst.edu/all-publications/
Paginación: /all-publications/page/1/ … /all-publications/page/342/
URLs publicaciones: /publications/[tipo]/[slug]/

Requisitos:
    pip install selenium webdriver-manager pandas beautifulsoup4

Uso:
    python lincoln_pdf_scraper.py

Salida:
    lincoln_pdfs.csv
"""

import re
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
BASE_URL    = "https://www.lincolninst.edu"
START_URL   = "https://www.lincolninst.edu/all-publications/"
OUTPUT_FILE = "lincoln_pdfs.csv"
DELAY       = 1.5    # entre páginas del listado
PUB_DELAY   = 1.5    # entre visitas a publicaciones

# Secciones genéricas a excluir (no son publicaciones individuales)
EXCLUDE_PATHS = {
    "/publications/",
    "/publications/books/",
    "/publications/policy-focus-reports-policy-briefs/",
    "/publications/policy-focus-reports/",
    "/publications/policy-briefs/",
    "/publications/working-conference-papers/",
    "/publications/working-papers/",
    "/publications/conference-papers/",
    "/publications/other/",
    "/publications/land-lines-magazine/",
}

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


def get_soup(driver, url, wait_selector=None):
    driver.get(url)
    if wait_selector:
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
            )
        except Exception:
            pass
    time.sleep(DELAY)
    return BeautifulSoup(driver.page_source, "html.parser")


def is_publication_url(href):
    """Devuelve True si el href apunta a una publicación individual."""
    if not href:
        return False
    # Debe contener /publications/ y no ser una sección genérica
    path = href.replace(BASE_URL, "")
    if "/publications/" not in path:
        return False
    # Excluir secciones genéricas
    for excl in EXCLUDE_PATHS:
        if path.rstrip("/") + "/" == excl or path == excl.rstrip("/"):
            return False
    # Debe tener al menos un segmento después del tipo
    # ej: /publications/books/titulo-del-libro/  → OK
    # ej: /publications/books/  → excluido
    parts = [p for p in path.strip("/").split("/") if p]
    return len(parts) >= 3  # ['publications', 'books', 'slug']


# ─────────────────────────────────────────────
# FASE 1 — Recolectar URLs de publicaciones
# ─────────────────────────────────────────────

def collect_publication_urls(driver):
    pub_urls = []

    print("=" * 60)
    print("FASE 1: Detectando número de páginas…")
    print("=" * 60)

    soup = get_soup(driver, START_URL, wait_selector="a[href*='/publications/']")

    # Detectar última página desde el paginador
    last_page = 1
    for a in soup.find_all("a", href=True):
        m = re.search(r"/all-publications/page/(\d+)/", a["href"])
        if m:
            last_page = max(last_page, int(m.group(1)))

    print(f"  → {last_page} páginas encontradas\n")
    print("=" * 60)
    print("Recolectando URLs…")
    print("=" * 60)

    # Recolectar página 1 (ya cargada)
    def extract_urls(soup):
        found = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if is_publication_url(href):
                full = href if href.startswith("http") else urljoin(BASE_URL, href)
                if full not in pub_urls and full not in found:
                    found.append(full)
        return found

    new_urls = extract_urls(soup)
    pub_urls.extend(new_urls)
    print(f"  Página 1/{last_page}: +{len(new_urls)}  (total: {len(pub_urls)})")

    # Iterar desde página 2 hasta la última
    for page_num in range(2, last_page + 1):
        url  = f"{BASE_URL}/all-publications/page/{page_num}/"
        print(f"  Página {page_num}/{last_page}: {url}")
        soup = get_soup(driver, url, wait_selector="a[href*='/publications/']")

        new_urls = extract_urls(soup)
        pub_urls.extend(new_urls)
        print(f"    +{len(new_urls)}  (total: {len(pub_urls)})")

    print(f"\n  ✅ Total publicaciones: {len(pub_urls)}\n")
    return pub_urls


# ─────────────────────────────────────────────
# FASE 2 — Visitar cada publicación y buscar PDF
# ─────────────────────────────────────────────

def collect_pdfs(driver, pub_urls):
    all_pdfs = []
    total    = len(pub_urls)

    print("=" * 60)
    print("FASE 2: Buscando PDFs…")
    print("=" * 60)

    for i, url in enumerate(pub_urls, 1):
        print(f"  [{i}/{total}] {url}")
        driver.get(url)
        time.sleep(PUB_DELAY)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Título
        h1    = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else url.split("/")[-2].replace("-", " ").title()

        # Fecha
        date = ""
        for sel in [".publication-date", "time", "[class*='date']", ".meta"]:
            tag = soup.select_one(sel)
            if tag:
                date = tag.get_text(strip=True)
                break

        # Tipo de publicación (inferido de la URL)
        parts    = url.replace(BASE_URL, "").strip("/").split("/")
        pub_type = parts[1].replace("-", " ").title() if len(parts) > 1 else ""

        # Buscar PDFs
        pdfs_found    = []
        seen_pdf_urls = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            full = urljoin(BASE_URL, href)
            text = a.get_text(strip=True)

            if href.lower().endswith(".pdf") and full not in seen_pdf_urls:
                seen_pdf_urls.add(full)
                pdfs_found.append((text or title, full))
            elif any(kw in text.lower() for kw in ["free download", "download pdf", "descargar"]) \
                    and full not in seen_pdf_urls:
                seen_pdf_urls.add(full)
                pdfs_found.append((text or title, full))

        if pdfs_found:
            for pdf_title, pdf_url in pdfs_found:
                all_pdfs.append({
                    "publication_title": title,
                    "pdf_title":         pdf_title,
                    "pdf_url":           pdf_url,
                    "publication_url":   url,
                    "publication_type":  pub_type,
                    "date":              date,
                })
            print(f"    ✅ {len(pdfs_found)} PDF(s)")
        else:
            print(f"    ⚠️  Sin PDF")
            all_pdfs.append({
                "publication_title": title,
                "pdf_title":         "",
                "pdf_url":           "",
                "publication_url":   url,
                "publication_type":  pub_type,
                "date":              date,
            })

    return all_pdfs


# ─────────────────────────────────────────────
# GUARDAR CSV
# ─────────────────────────────────────────────

def save_csv(data):
    df      = pd.DataFrame(data)
    df_pdfs = df[df["pdf_url"] != ""].drop_duplicates(subset=["pdf_url"])
    df_all  = df.drop_duplicates(subset=["publication_url"])
    df_pdfs.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n✅ Guardado: {OUTPUT_FILE}")
    print(f"   Publicaciones procesadas:  {len(df_all)}")
    print(f"   PDFs únicos:               {len(df_pdfs)}")
    print(f"   Sin PDF:                   {len(df_all) - len(df[df['pdf_url'] != ''].drop_duplicates(subset=['publication_url']))}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🔍 Lincoln Institute — PDF Scraper")
    print(f"Sitio: {START_URL}\n")

    driver = init_driver()
    try:
        pub_urls = collect_publication_urls(driver)
        if pub_urls:
            pdfs = collect_pdfs(driver, pub_urls)
            save_csv(pdfs)
        else:
            print("\n[AVISO] No se encontraron publicaciones.")
    finally:
        driver.quit()
        print("\nNavegador cerrado.")