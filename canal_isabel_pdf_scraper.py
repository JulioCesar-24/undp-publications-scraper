"""
Canal de Isabel II — PDF Scraper
=================================
Sitio: https://www.canaldeisabelsegunda.es/publicaciones

El sitio es HTML estático — todas las publicaciones (109+) están en una sola
página. El botón "Ver más publicaciones" es solo un toggle JavaScript sobre
contenido ya cargado, así que no necesita Selenium.

Cada publicación está en un <div class="block-notices notice"> con:
  - data-categoria="..."  → categoría (revista, corporativas, ...)
  - data-fecha="YYYY-MM-DD" → fecha
  - <a href="...pdf...">  → enlace directo al PDF
  - <h4>                  → título
  - <h3 class="title-notice"> → categoría visible

Requisitos:
    pip install requests beautifulsoup4 pandas

Uso:
    python canal_isabel_pdf_scraper.py

Salida:
    canal_isabel_pdfs.csv
"""

import requests
import pandas as pd
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
BASE_URL    = "https://www.canaldeisabelsegunda.es"
START_URL   = "https://www.canaldeisabelsegunda.es/publicaciones"
OUTPUT_FILE = "canal_isabel_pdfs.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ─────────────────────────────────────────────
# SCRAPING
# ─────────────────────────────────────────────

def get_soup(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return BeautifulSoup(resp.text, "html.parser")


def extract_publications(soup):
    results = []
    seen_pdf_urls = set()

    blocks = soup.select("div.block-notices.notice")
    print(f"  → {len(blocks)} bloques de publicación encontrados")

    for block in blocks:
        # Categoría y fecha desde atributos data-*
        category = block.get("data-categoria", "").strip()
        date     = block.get("data-fecha", "").strip()

        # Enlace al PDF
        a = block.find("a", href=True)
        if not a:
            continue
        pdf_url = urljoin(BASE_URL, a["href"])

        # Filtrar duplicados
        if pdf_url in seen_pdf_urls:
            continue
        seen_pdf_urls.add(pdf_url)

        # Título: <h4> dentro del bloque (a veces con <p> dentro)
        h4    = block.find("h4")
        title = h4.get_text(strip=True) if h4 else ""

        # Categoría visible (si no había data-categoria)
        if not category:
            h3 = block.find("h3", class_="title-notice")
            if h3:
                category = h3.get_text(strip=True)

        # Fallback de título: nombre del archivo
        if not title:
            title = a.get_text(strip=True) or pdf_url.rsplit("/", 1)[-1]

        results.append({
            "publication_title": title,
            "pdf_title":         title,
            "pdf_url":           pdf_url,
            "publication_url":   START_URL,
            "publication_type":  category,
            "date":              date,
        })

    return results


# ─────────────────────────────────────────────
# GUARDAR CSV
# ─────────────────────────────────────────────

def save_csv(data):
    df = pd.DataFrame(data).drop_duplicates(subset=["pdf_url"])
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n✅ Guardado: {OUTPUT_FILE}")
    print(f"   PDFs únicos: {len(df)}")
    if "publication_type" in df.columns:
        print("\n   Distribución por categoría:")
        for cat, n in df["publication_type"].value_counts().items():
            print(f"     {cat or '(sin categoría)':<25} {n}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🔍 Canal de Isabel II — PDF Scraper")
    print(f"Sitio: {START_URL}\n")
    print("=" * 60)
    print("Descargando página de publicaciones…")
    print("=" * 60)

    soup = get_soup(START_URL)
    pdfs = extract_publications(soup)

    if pdfs:
        save_csv(pdfs)
    else:
        print("\n[AVISO] No se encontraron publicaciones.")
