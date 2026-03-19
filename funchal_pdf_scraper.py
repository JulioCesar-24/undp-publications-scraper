"""
Câmara Municipal do Funchal — PDF Scraper
==========================================
Sitio: https://cmfdoc.funchal.pt

El sitio es HTML estático — no necesita Selenium.
Recorre todas las secciones del menú y extrae los PDFs directamente.

Requisitos:
    pip install requests beautifulsoup4 pandas

Uso:
    python funchal_pdf_scraper.py

Salida:
    funchal_pdfs.csv
"""

import time
import requests
import pandas as pd
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
BASE_URL    = "https://cmfdoc.funchal.pt"
OUTPUT_FILE = "funchal_pdfs.csv"
DELAY       = 1.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Todas las secciones del sitio con sus URLs y categoría
SECTIONS = [
    # Câmara Municipal
    ("Câmara Municipal / Atas",             "/reunioes-de-camara/rc-atas.html"),
    ("Câmara Municipal / Regimento",        "/reunioes-de-camara/rc-regimento.html"),
    ("Câmara Municipal / Convocatórias",    "/reunioes-de-camara/rc-convocatorias.html"),
    ("Câmara Municipal / Editais",          "/reunioes-de-camara/rc-editais.html"),
    # Documentos Financeiros
    ("Doc. Financeiros / Orçamento",        "/doc-financeiros/orcamento.html"),
    ("Doc. Financeiros / Prestação Contas", "/doc-financeiros/prestacao-de-contas.html"),
    ("Doc. Financeiros / Auditorias",       "/doc-financeiros/auditorias.html"),
    ("Doc. Financeiros / Subvenções",       "/doc-financeiros/subven%C3%A7%C3%B5es.html"),
    ("Doc. Financeiros / PAEL",             "/doc-financeiros/pael.html"),
    # Editais / Publicitações
    ("Publicitações / Qualidade Água",      "/publicita%C3%A7%C3%B5es/mm-editais-controlo-da-qualidade-da-agua.html"),
    ("Publicitações / Planeamento",         "/publicita%C3%A7%C3%B5es/dep-planeamento-e-ordenamento.html"),
    ("Publicitações / Cemitérios",          "/publicita%C3%A7%C3%B5es/mm-editais-cemiterios.html"),
    ("Publicitações / Urbanismo",           "/publicita%C3%A7%C3%B5es/urbanismo.html"),
    ("Publicitações / Div. Administrativa", "/publicita%C3%A7%C3%B5es/mm-editais-div-administrativa-e-de-obras-particulares.html"),
    ("Publicitações / Fiscalização",        "/publicita%C3%A7%C3%B5es/editais-da-fiscaliza%C3%A7%C3%A3o.html"),
    ("Publicitações / Mercados Municipais", "/publicita%C3%A7%C3%B5es/mm-editais-mercados-municipais.html"),
    ("Publicitações / Trânsito",            "/publicita%C3%A7%C3%B5es/mm-editais-transito.html"),
    ("Publicitações / Ordenamento",         "/publicita%C3%A7%C3%B5es/mm-ordenamento-territorio.html"),
    ("Publicitações / Outros Editais",      "/publicita%C3%A7%C3%B5es/mm-outros-editais.html"),
    ("Publicitações / Eleições",            "/publicita%C3%A7%C3%B5es/mm-editais-eleicoes.html"),
    ("Publicitações / Concursos Decorrer",  "/publicita%C3%A7%C3%B5es/concursos/a-decorrer.html"),
    ("Publicitações / Concursos Concluídos","/publicita%C3%A7%C3%B5es/concursos/conclu%C3%ADdos.html"),
    # Outros
    ("Regulamentos",                        "/regulamentos.html"),
    ("Impostos e Taxas",                    "/impostos-e-taxas.html"),
    ("PPRGCIC",                             "/plano-de-prevencao.html"),
    ("Contratos Interadministrativos",      "/contratos-interadministrativos.html"),
    # Assembleia Municipal
    ("Assembleia / Regimento",              "/ass-municipal/am-regimento.html"),
    ("Assembleia / Convocatórias",          "/ass-municipal/am-convocatorias.html"),
    ("Assembleia / Atas",                   "/ass-municipal/am-atas.html"),
    ("Assembleia / Deliberações",           "/ass-municipal/am-deliberacoes.html"),
]

# ─────────────────────────────────────────────
# SCRAPING
# ─────────────────────────────────────────────

def get_soup(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"    [ERROR] {e}")
        return None


def extract_pdfs_from_page(url, category):
    """Extrae todos los PDFs de una página de sección."""
    soup = get_soup(url)
    if not soup:
        return []

    results = []
    seen    = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" not in href.lower():
            continue

        pdf_url = urljoin(BASE_URL, href)
        if pdf_url in seen:
            continue
        seen.add(pdf_url)

        # Título: buscar h4/h3/h2 hermano o padre más cercano
        title = ""
        # Subir al padre y buscar heading cercano
        parent = a.parent
        for _ in range(4):
            if parent is None:
                break
            heading = parent.find(["h4", "h3", "h2", "h5"])
            if heading:
                title = heading.get_text(strip=True)
                break
            parent = parent.parent

        # Si no encontró título, usar el texto del enlace o el nombre del archivo
        if not title:
            title = a.get_text(strip=True)
        if not title:
            title = href.split("/")[-1].replace(".pdf", "").replace("_", " ").replace("-", " ")

        # Fecha: buscar elemento de fecha cercano
        date = ""
        parent = a.parent
        for _ in range(5):
            if parent is None:
                break
            date_tag = parent.find(class_=lambda c: c and "date" in c.lower()) or \
                       parent.find("span") or parent.find("p")
            if date_tag:
                text = date_tag.get_text(strip=True)
                # Validar que parece una fecha (tiene dígitos y longitud razonable)
                if any(c.isdigit() for c in text) and 6 <= len(text) <= 30:
                    date = text
                    break
            parent = parent.parent

        results.append({
            "category":   category,
            "title":      title,
            "pdf_url":    pdf_url,
            "source_url": url,
            "date":       date,
        })

    return results


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🔍 Câmara Municipal do Funchal — PDF Scraper")
    print(f"Sitio: {BASE_URL}\n")
    print("=" * 60)

    all_pdfs = []

    for category, path in SECTIONS:
        url = urljoin(BASE_URL, path)
        print(f"  {category}")
        print(f"  → {url}")

        pdfs = extract_pdfs_from_page(url, category)
        all_pdfs.extend(pdfs)
        print(f"    ✅ {len(pdfs)} PDFs encontrados\n")

        time.sleep(DELAY)

    # Guardar CSV
    if all_pdfs:
        df = pd.DataFrame(all_pdfs).drop_duplicates(subset=["pdf_url"])
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        print("=" * 60)
        print(f"✅ Guardado: {OUTPUT_FILE}")
        print(f"   Total PDFs únicos: {len(df)}")
        print(f"   Secciones procesadas: {len(SECTIONS)}")
    else:
        print("[AVISO] No se encontraron PDFs.")