"""
UNDP Publications PDF Scraper
==============================
Extrae todos los links de PDFs de:
https://www.undp.org/publications

Requisitos:
    pip install requests beautifulsoup4 selenium webdriver-manager pandas

Uso:
    python undp_pdf_scraper.py

Salida:
    undp_pdfs.csv  →  columnas: title, pdf_url, publication_url, date
"""

import csv
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
BASE_URL = "https://www.undp.org"
START_URL = "https://www.undp.org/publications?combine=&sort_by=field_display_date_value"
OUTPUT_FILE = "undp_pdfs.csv"
DELAY_SECONDS = 1.5          # pausa entre peticiones (ser amable con el servidor)
MAX_PAGES = 200              # límite de seguridad de páginas a recorrer
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def get_soup(url: str) -> BeautifulSoup | None:
    """Descarga una página y devuelve su BeautifulSoup."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"  [ERROR] {url} → {e}")
        return None


def find_pdf_links(soup: BeautifulSoup, page_url: str) -> list[dict]:
    """Encuentra todos los <a> cuyo href termina en .pdf en una página."""
    results = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            full_url = urljoin(BASE_URL, href)
            title = a.get_text(strip=True) or a.get("title", "") or "Sin título"
            results.append({"title": title, "pdf_url": full_url, "source_page": page_url})
    return results


def get_next_page_url(soup: BeautifulSoup, current_url: str) -> str | None:
    """Devuelve la URL de la siguiente página de paginación, o None si no existe."""
    # Busca enlace 'Next' o '›' o botón de paginación
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True).lower()
        rel  = a.get("rel", [])
        aria = a.get("aria-label", "").lower()
        if text in ("next", "›", "siguiente") or "next" in rel or "next" in aria:
            return urljoin(BASE_URL, a["href"])
    return None


# ─────────────────────────────────────────────
# FASE 1 – Recolectar URLs de publicaciones
# ─────────────────────────────────────────────

def collect_publication_urls() -> list[str]:
    """Recorre todas las páginas del listado y devuelve las URLs de publicaciones."""
    pub_urls = []
    current_url = START_URL
    page_num = 0

    print("=" * 60)
    print("FASE 1: Recorriendo páginas del listado…")
    print("=" * 60)

    while current_url and page_num < MAX_PAGES:
        page_num += 1
        print(f"  Página {page_num}: {current_url}")
        soup = get_soup(current_url)
        if not soup:
            break

        # Ajusta el selector según la estructura real del sitio
        cards = soup.select("article, .views-row, .publication-card, h3 a, h2 a")
        for card in cards:
            # Si el elemento es un <a> con href
            if card.name == "a" and card.get("href"):
                href = card["href"]
            else:
                # busca primer enlace dentro del bloque
                a = card.find("a", href=True)
                href = a["href"] if a else None

            if href:
                full = urljoin(BASE_URL, href)
                # Filtrar solo rutas de publicaciones del mismo dominio
                if urlparse(full).netloc == urlparse(BASE_URL).netloc:
                    if full not in pub_urls:
                        pub_urls.append(full)

        next_url = get_next_page_url(soup, current_url)
        current_url = next_url
        time.sleep(DELAY_SECONDS)

    print(f"\n  → {len(pub_urls)} URLs de publicaciones encontradas.\n")
    return pub_urls


# ─────────────────────────────────────────────
# FASE 2 – Visitar cada publicación y buscar PDF
# ─────────────────────────────────────────────

def collect_pdfs_from_publications(pub_urls: list[str]) -> list[dict]:
    """Visita cada publicación y extrae los enlaces a PDF."""
    all_pdfs = []
    total = len(pub_urls)

    print("=" * 60)
    print("FASE 2: Buscando PDFs en cada publicación…")
    print("=" * 60)

    for i, url in enumerate(pub_urls, 1):
        print(f"  [{i}/{total}] {url}")
        soup = get_soup(url)
        if not soup:
            continue

        # Título de la publicación (desde la página de detalle)
        title_tag = soup.find("h1") or soup.find("title")
        pub_title = title_tag.get_text(strip=True) if title_tag else "Sin título"

        # Fecha (intenta varias estructuras comunes)
        date = ""
        date_tag = soup.find(class_=re.compile(r"date|time|published", re.I))
        if date_tag:
            date = date_tag.get_text(strip=True)

        pdfs = find_pdf_links(soup, url)

        if pdfs:
            for pdf in pdfs:
                all_pdfs.append({
                    "publication_title": pub_title,
                    "pdf_title": pdf["title"],
                    "pdf_url": pdf["pdf_url"],
                    "publication_url": url,
                    "date": date,
                })
        else:
            # No se encontró PDF directo — registrar igualmente para revisión manual
            all_pdfs.append({
                "publication_title": pub_title,
                "pdf_title": "",
                "pdf_url": "",
                "publication_url": url,
                "date": date,
            })

        time.sleep(DELAY_SECONDS)

    return all_pdfs


# ─────────────────────────────────────────────
# ALTERNATIVA: modo rápido (solo busca PDFs en el listado)
# ─────────────────────────────────────────────

def quick_scan_listing_pages() -> list[dict]:
    """
    Modo rápido: busca PDFs directamente en las páginas del listado
    sin entrar a cada publicación.  Útil si los links ya están en el listado.
    """
    all_pdfs = []
    current_url = START_URL
    page_num = 0

    print("=" * 60)
    print("MODO RÁPIDO: Buscando PDFs en páginas del listado…")
    print("=" * 60)

    while current_url and page_num < MAX_PAGES:
        page_num += 1
        print(f"  Página {page_num}: {current_url}")
        soup = get_soup(current_url)
        if not soup:
            break

        pdfs = find_pdf_links(soup, current_url)
        all_pdfs.extend(pdfs)
        print(f"    → {len(pdfs)} PDFs encontrados en esta página")

        current_url = get_next_page_url(soup, current_url)
        time.sleep(DELAY_SECONDS)

    return all_pdfs


# ─────────────────────────────────────────────
# GUARDAR CSV
# ─────────────────────────────────────────────

def save_to_csv(data: list[dict], filename: str):
    if not data:
        print("\n[AVISO] No se encontraron datos para guardar.")
        return

    df = pd.DataFrame(data)
    # Eliminar duplicados por pdf_url
    df = df[df["pdf_url"] != ""].drop_duplicates(subset=["pdf_url"])
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"\n✅ CSV guardado: {filename}  ({len(df)} PDFs únicos)")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🔍 UNDP PDF Scraper")
    print("Sitio:", START_URL)
    print()

    # ── ELIGE EL MODO ──────────────────────────────────────────
    # MODO A (recomendado): entra a cada publicación para buscar PDFs
    # MODO B (rápido): solo escanea el listado principal
    # Descomenta el que quieras usar:

    MODE = "A"   # Cambia a "B" para el modo rápido

    if MODE == "A":
        pub_urls = collect_publication_urls()
        pdfs     = collect_pdfs_from_publications(pub_urls)
        save_to_csv(pdfs, OUTPUT_FILE)
    else:
        pdfs = quick_scan_listing_pages()
        # En modo rápido los campos son distintos
        df = pd.DataFrame(pdfs).drop_duplicates(subset=["pdf_url"])
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        print(f"\n✅ CSV guardado: {OUTPUT_FILE}  ({len(df)} PDFs únicos)")

    print("\nColumnas del CSV generado:")
    for col in ["publication_title", "pdf_title", "pdf_url", "publication_url", "date"]:
        print(f"  • {col}")