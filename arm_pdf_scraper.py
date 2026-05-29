"""
ARM — Águas e Resíduos da Madeira — PDF Scraper
================================================
Sitio: https://arm.pt/empresa/

HTML estático — usa requests, sin Selenium.
Todos los PDFs están en una sola página con secciones por ancla (#).

Requisitos:
    pip install requests beautifulsoup4 pandas

Uso:
    python arm_pdf_scraper.py

Salida:
    arm_pdfs.csv
"""

import time
import requests
import pandas as pd
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
BASE_URL    = "https://arm.pt"
TARGET_URL  = "https://arm.pt/empresa/"
OUTPUT_FILE = "arm_pdfs.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Mapeo de anclas a categorías (en el orden que aparecen en la página)
SECTION_ANCHORS = {
    "relatorioecontas": "Relatórios e Contas",
    "regulamentos":     "Regulamentos",
    "qualidade":        "Qualidade, Ambiente e Segurança",
    "gestaoderiscos":   "Gestão de Riscos de Corrupção",
    "estutosarm":       "Estatutos ARM",
    "codigodeconduta":  "Código de Conduta",
    "planoigualdade":   "Plano para a Igualdade",
    "protecaodados":    "Proteção de Dados",
    "canaldenuncia":    "Canal de Denúncia",
    "projetoseobras":   "Projetos e Obras",
    "contratospublicos":"Contratos Públicos",
}

# ─────────────────────────────────────────────
# SCRAPING
# ─────────────────────────────────────────────

def get_soup(url):
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return BeautifulSoup(resp.text, "html.parser")


def scrape():
    print(f"\n🔍 ARM — PDF Scraper")
    print(f"Sitio: {TARGET_URL}\n")
    print("=" * 60)
    print("Descargando página…")

    soup = get_soup(TARGET_URL)
    all_pdfs = []
    seen     = set()

    # Recorrer todos los <a> con .pdf
    # Para cada PDF, determinar su categoría buscando el h2 más cercano anterior
    current_category = "General"

    for tag in soup.find_all(["h2", "h3", "a"]):
        # Actualizar categoría cuando encontramos un heading
        if tag.name in ("h2", "h3"):
            heading_text = tag.get_text(strip=True)
            # Buscar si el id o texto coincide con alguna sección conocida
            tag_id = tag.get("id", "").lower()
            matched = False
            for anchor, cat_name in SECTION_ANCHORS.items():
                if anchor in tag_id or anchor in heading_text.lower().replace(" ", "").replace(",", ""):
                    current_category = cat_name
                    matched = True
                    break
            if not matched and heading_text:
                current_category = heading_text

        # Extraer PDF
        elif tag.name == "a" and tag.get("href", ""):
            href = tag["href"].strip()
            if href.lower().endswith(".pdf"):
                full_url = href if href.startswith("http") else urljoin(BASE_URL, href)
                if full_url in seen:
                    continue
                seen.add(full_url)

                pdf_title = tag.get_text(strip=True) or full_url.split("/")[-1].replace(".pdf", "").replace("-", " ").replace("_", " ")

                all_pdfs.append({
                    "category":  current_category,
                    "pdf_title": pdf_title,
                    "pdf_url":   full_url,
                    "source_url": TARGET_URL,
                })

    return all_pdfs


def save_csv(data):
    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n✅ Guardado: {OUTPUT_FILE}")
    print(f"   PDFs únicos: {len(df)}")
    print(f"\n   Por categoría:")
    for cat, grp in df.groupby("category"):
        print(f"     • {cat}: {len(grp)} PDF(s)")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    pdfs = scrape()
    if pdfs:
        save_csv(pdfs)
    else:
        print("[AVISO] No se encontraron PDFs.")