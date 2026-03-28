"""
EU Environment Publications — PDF Scraper
==========================================
Sitio: https://environment.ec.europa.eu/publications_en
Total: ~356 publicaciones en 36 páginas (?page=0..35)

Estrategia:
  1. Recorrer las 36 páginas del listado con requests
  2. Recolectar URLs de publicaciones individuales
  3. Visitar cada publicación y extraer PDFs

Requisitos:
    pip install requests beautifulsoup4 pandas

Uso:
    python eu_environment_pdf_scraper.py

Salida:
    eu_environment_pdfs.csv
"""

import time
import requests
import pandas as pd
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
BASE_URL    = "https://environment.ec.europa.eu"
LIST_URL    = "https://environment.ec.europa.eu/publications_en"
OUTPUT_FILE = "eu_environment_pdfs.csv"
DELAY       = 1.2   # entre peticiones (respetar servidor EU)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def get_soup(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"    [ERROR] {e}")
        return None

# ─────────────────────────────────────────────
# FASE 1 — Recolectar URLs + metadatos del listado
# ─────────────────────────────────────────────

def collect_publication_urls():
    pub_data = []   # lista de dicts con url, title, pub_type, date
    seen     = set()

    print("=" * 60)
    print("FASE 1: Detectando número de páginas…")
    print("=" * 60)

    # Cargar página 1 para detectar total de páginas
    soup = get_soup(LIST_URL)
    if not soup:
        return []

    # Detectar última página
    last_page = 0
    for a in soup.find_all("a", href=True):
        import re
        m = re.search(r"\?page=(\d+)", a["href"])
        if m:
            last_page = max(last_page, int(m.group(1)))

    total_pages = last_page + 1
    print(f"  → {total_pages} páginas  (~{total_pages * 10} publicaciones)\n")

    print("=" * 60)
    print("Recolectando publicaciones…")
    print("=" * 60)

    def parse_listing_page(soup, page_num):
        """Extrae publicaciones de una página de listado."""
        found = []
        # Las publicaciones están en articles o en bloques con clase específica
        # Buscar todos los links que apunten a /publications/..._en
        import re
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full = href if href.startswith("http") else urljoin(BASE_URL, href)
            # URL de publicación individual: termina en _en y contiene /publications/
            if ("/publications/" in full
                    and full.endswith("_en")
                    and full not in seen
                    and "publications_en" not in full):
                seen.add(full)
                title = a.get_text(strip=True)
                # Buscar metadatos en el contenedor padre
                parent = a.parent
                pub_type = ""
                date     = ""
                for _ in range(6):
                    if parent is None:
                        break
                    # Tipo de publicación
                    type_tag = parent.find(class_=lambda c: c and "type" in c.lower())
                    if type_tag and not pub_type:
                        pub_type = type_tag.get_text(strip=True)
                    # Fecha
                    time_tag = parent.find("time") or parent.find(class_=lambda c: c and "date" in c.lower() if c else False)
                    if time_tag and not date:
                        date = time_tag.get("datetime", "") or time_tag.get_text(strip=True)
                    parent = parent.parent

                found.append({
                    "title":        title,
                    "pub_url":      full,
                    "pub_type":     pub_type,
                    "date":         date,
                })
        return found

    # Página 1 (ya cargada)
    results = parse_listing_page(soup, 0)
    pub_data.extend(results)
    print(f"  Página 1/{total_pages}: +{len(results)}  (total: {len(pub_data)})")
    time.sleep(DELAY)

    # Páginas 2..N
    for page_num in range(1, total_pages):
        url  = f"{LIST_URL}?page={page_num}"
        print(f"  Página {page_num + 1}/{total_pages}: {url}")
        soup = get_soup(url)
        if not soup:
            continue
        results = parse_listing_page(soup, page_num)
        pub_data.extend(results)
        print(f"    +{len(results)}  (total: {len(pub_data)})")
        time.sleep(DELAY)

    print(f"\n  ✅ Total publicaciones: {len(pub_data)}\n")
    return pub_data


# ─────────────────────────────────────────────
# FASE 2 — Visitar cada publicación y buscar PDFs
# ─────────────────────────────────────────────

def collect_pdfs(pub_data):
    all_pdfs = []
    total    = len(pub_data)

    print("=" * 60)
    print("FASE 2: Buscando PDFs en cada publicación…")
    print("=" * 60)

    # Dominios de la Comisión Europea donde pueden estar los PDFs
    EU_DOMAINS = [
        "environment.ec.europa.eu",
        "op.europa.eu",
        "eur-lex.europa.eu",
        "ec.europa.eu",
        "europa.eu",
    ]

    for i, pub in enumerate(pub_data, 1):
        url   = pub["pub_url"]
        title = pub["title"]
        print(f"  [{i}/{total}] {title[:65]}")

        soup = get_soup(url)
        if not soup:
            all_pdfs.append({**pub, "pdf_title": "", "pdf_url": ""})
            continue

        # Título más preciso desde la página de detalle
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

        # Buscar PDFs: .pdf en href o links de descarga de op.europa.eu
        pdfs_found    = []
        seen_pdf_urls = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            text = a.get_text(strip=True)
            full = href if href.startswith("http") else urljoin(BASE_URL, href)

            is_pdf = (
                href.lower().endswith(".pdf") or
                "format=pdf" in href.lower() or
                "/publication-detail/" in href.lower() and any(d in href for d in EU_DOMAINS) or
                ("download" in text.lower() and any(d in full for d in EU_DOMAINS))
            )

            if is_pdf and full not in seen_pdf_urls:
                seen_pdf_urls.add(full)
                pdfs_found.append((text or title, full))

        if pdfs_found:
            for pdf_title, pdf_url in pdfs_found:
                all_pdfs.append({
                    **pub,
                    "pdf_title": pdf_title,
                    "pdf_url":   pdf_url,
                })
            print(f"    ✅ {len(pdfs_found)} PDF(s)")
        else:
            print(f"    ⚠️  Sin PDF directo")
            all_pdfs.append({**pub, "pdf_title": "", "pdf_url": ""})

        time.sleep(DELAY)

    return all_pdfs


# ─────────────────────────────────────────────
# GUARDAR CSV
# ─────────────────────────────────────────────

def save_csv(data):
    df      = pd.DataFrame(data)
    df_pdfs = df[df["pdf_url"] != ""].drop_duplicates(subset=["pdf_url"])
    df_all  = df.drop_duplicates(subset=["pub_url"])
    df_pdfs.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n✅ Guardado: {OUTPUT_FILE}")
    print(f"   Publicaciones procesadas: {len(df_all)}")
    print(f"   PDFs únicos:              {len(df_pdfs)}")
    print(f"   Sin PDF:                  {len(df_all) - len(df[df['pdf_url'] != ''].drop_duplicates(subset=['pub_url']))}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🔍 EU Environment Publications — PDF Scraper")
    print(f"Sitio: {LIST_URL}\n")

    pub_data = collect_publication_urls()
    if pub_data:
        pdfs = collect_pdfs(pub_data)
        save_csv(pdfs)
    else:
        print("\n[AVISO] No se encontraron publicaciones.")