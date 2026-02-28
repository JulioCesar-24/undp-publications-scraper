import { chromium, Page } from "playwright";
import * as fs from "fs";

const BASE = "https://www.undp.org";

interface PublicationRow {
  title: string;
  date: string;
  pdf: string;
  url: string;
}

// 🔹 Extrae links de las publicaciones de la página de listado
async function scrapeListing(page: Page, pageNumber: number): Promise<string[]> {
  const url = `${BASE}/publications?page=${pageNumber}`;
  console.log(`📄 Scrapeando listado página ${pageNumber}...`);

  await page.goto(url, { waitUntil: "domcontentloaded" });

  // Espera que carguen los resultados reales
  try {
    await page.waitForSelector(".views-row", { timeout: 15000 });
  } catch {
    console.log("⚠ No se encontraron publicaciones en esta página.");
    return [];
  }

  // Extrae los links de cada publicación
  const links = await page.$$eval(
    ".views-row h3 a",
    anchors => anchors.map(a => (a as HTMLAnchorElement).href)
  );

  return links;
}

// 🔹 Extrae título, fecha y PDFs de cada publicación
async function scrapeDetail(page: Page, url: string): Promise<PublicationRow[]> {
  try {
    await page.goto(url, { waitUntil: "domcontentloaded" });

    const title = (await page.locator("h1").first().innerText()).trim();

    let date = "";
    const timeLocator = page.locator("time").first();
    if (await timeLocator.count()) {
      date = (await timeLocator.innerText()).trim();
    }

    const pdfLinks = await page.$$eval("a[href$='.pdf']", anchors =>
      anchors.map(a => (a as HTMLAnchorElement).href)
    );

    if (pdfLinks.length === 0) {
      return [{ title, date, pdf: "", url }];
    }

    return pdfLinks.map(pdf => ({
      title,
      date,
      pdf,
      url
    }));
  } catch (error) {
    console.log(`⚠ Error procesando ${url}`);
    return [];
  }
}

// 🔹 Función principal
async function main() {
  const browser = await chromium.launch({
    headless: false, // visible para debug; cambiar a true cuando funcione
    slowMo: 50 // simula interacción humana
  });

  const context = await browser.newContext({
    userAgent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
  });

  const page = await context.newPage();

  const visited = new Set<string>();
  const results: PublicationRow[] = [];

  let pageNumber = 0;

  while (true) {
    const links = await scrapeListing(page, pageNumber);

    if (!links || links.length === 0) {
      console.log("✅ No hay más páginas.");
      break;
    }

    for (const link of links) {
      if (!visited.has(link)) {
        visited.add(link);

        console.log("➡ Procesando:", link);

        const rows = await scrapeDetail(page, link);
        results.push(...rows);

        await page.waitForTimeout(300); // pausa para comportamiento humano
      }
    }

    pageNumber++;
  }

  // 🔹 Generar CSV
  const csvRows = [
    ["Título", "Fecha", "PDF", "URL"],
    ...results.map(r => [r.title, r.date, r.pdf, r.url])
  ];

  fs.writeFileSync(
    "undp_publicaciones_pdfs.csv",
    csvRows
      .map(row =>
        row.map(field => `"${field.replace(/"/g, '""')}"`).join(",")
      )
      .join("\n"),
    "utf-8"
  );

  console.log(`🎉 CSV generado con ${results.length} registros.`);

  await browser.close();
}

// 🔹 Ejecutar
main();







