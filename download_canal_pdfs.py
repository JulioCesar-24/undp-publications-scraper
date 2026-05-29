"""
Descarga todos los PDFs de canal_isabel_pdfs.csv organizados por categoría
y genera un ZIP por categoría.
"""

import csv
import os
import re
import sys
import time
import zipfile
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

CSV_FILE   = "canal_isabel_pdfs.csv"
OUT_DIR    = "canal_isabel_pdfs"
ZIP_DIR    = "canal_isabel_zips"
WORKERS    = 4
TIMEOUT    = 120

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def slugify(text, maxlen=80):
    text = re.sub(r"[^\w\s.-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "_", text).strip("._-")
    return text[:maxlen] or "publicacion"


def load_rows():
    with open(CSV_FILE, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def download(row):
    url      = row["pdf_url"]
    category = row.get("publication_type") or "sin-categoria"
    date     = row.get("date") or ""
    title    = row.get("publication_title") or "publicacion"

    cat_dir = os.path.join(OUT_DIR, slugify(category, 40))
    os.makedirs(cat_dir, exist_ok=True)

    fname = f"{date}_{slugify(title)}.pdf" if date else f"{slugify(title)}.pdf"
    path  = os.path.join(cat_dir, fname)

    if os.path.exists(path) and os.path.getsize(path) > 1024:
        return ("skip", path, 0)

    try:
        with requests.get(url, headers=HEADERS, stream=True, timeout=TIMEOUT) as r:
            r.raise_for_status()
            size = 0
            with open(path, "wb") as out:
                for chunk in r.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        out.write(chunk)
                        size += len(chunk)
        return ("ok", path, size)
    except Exception as e:
        if os.path.exists(path):
            os.remove(path)
        return ("err", url, str(e))


def main():
    rows = load_rows()
    total = len(rows)
    print(f"📥 Descargando {total} PDFs con {WORKERS} hilos...")
    print("=" * 60)

    os.makedirs(OUT_DIR, exist_ok=True)

    done = 0
    bytes_total = 0
    errors = []
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(download, row): row for row in rows}
        for fut in as_completed(futures):
            status, path, info = fut.result()
            done += 1
            if status == "ok":
                bytes_total += info
                print(f"  [{done:3}/{total}] ✅ {os.path.relpath(path, OUT_DIR)}  ({info/1024/1024:.1f} MB)")
            elif status == "skip":
                print(f"  [{done:3}/{total}] ⏭️  {os.path.relpath(path, OUT_DIR)} (ya existe)")
            else:
                errors.append((path, info))
                print(f"  [{done:3}/{total}] ❌ {path[:80]}  -> {info}")

    dt = time.time() - t0
    print("=" * 60)
    print(f"\n✅ Descarga completada en {dt:.1f}s")
    print(f"   {bytes_total/1024/1024:.1f} MB descargados")
    if errors:
        print(f"\n⚠️  {len(errors)} errores:")
        for u, e in errors:
            print(f"    {u}  -> {e}")

    # ── Crear un ZIP por categoría ──
    print("\n📦 Creando ZIPs por categoría...")
    os.makedirs(ZIP_DIR, exist_ok=True)
    for cat in sorted(os.listdir(OUT_DIR)):
        cat_path = os.path.join(OUT_DIR, cat)
        if not os.path.isdir(cat_path):
            continue
        zip_path = os.path.join(ZIP_DIR, f"{cat}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            for fname in sorted(os.listdir(cat_path)):
                fpath = os.path.join(cat_path, fname)
                if os.path.isfile(fpath):
                    zf.write(fpath, arcname=os.path.join(cat, fname))
        size_mb = os.path.getsize(zip_path) / 1024 / 1024
        print(f"  ✅ {zip_path}  ({size_mb:.1f} MB)")

    print(f"\n✅ ZIPs listos en: {ZIP_DIR}/")


if __name__ == "__main__":
    main()
