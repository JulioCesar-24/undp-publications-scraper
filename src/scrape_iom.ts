import { chromium, Page } from "playwright";
import * as fs from "fs";

const BASE = "https://publications.iom.int/search";
const MAX_CONCURRENCY = 8; // Ajusta entre 5 y 12 según tu máquina

interface PublicationRow {
  title: string;
  date: string;
  pdf: string;
  url: string;
}

async function scrapeListing(page: Page, pageNumber: number): Promise<string[]> {
  const url = `${BASE}?search=&page=${pageNumber}`;
  console.log(`📄 Scrapeando listado página ${pageNumber}...`);

  await page.goto(url, { waitUntil: "networkidle" });

  try {
    await page.waitForSelector(".views-row", { timeout: 15000 });
  } catch {
    console.log("⚠ No se encontraron publicaciones en esta página.");
    return [];
  }

  return await page.$$eval(
    ".views-row .views-field-title a",
    anchors => anchors.map(a => (a as HTMLAnchorElement).href)
  );
}

async function scrapeDetail(page: Page, url: string): Promise<PublicationRow[]> {
  try {
    await page.goto(url, { waitUntil: "networkidle" });

    const title = (await page.locator("h1").first().innerText()).trim();

    let date = "";
    const timeLocator = page.locator("time").first();
    if (await timeLocator.count()) {
      date = (await timeLocator.innerText()).trim();
    }

    const pdfLinks = await page.$$eval("a[href*='.pdf']", anchors =>
      anchors.map(a =>
        new URL((a as HTMLAnchorElement).href, (window as any).location.origin).href
      )
    );

    if (pdfLinks.length === 0) {
      return [{ title, date, pdf: "", url }];
    }

    return pdfLinks.map(pdf => ({ title, date, pdf, url }));
  } catch {
    console.log(`⚠ Error procesando ${url}`);
    return [];
  }
}

async function main() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();

  const listPage = await context.newPage();

  const visited = new Set<string>();
  const results: PublicationRow[] = [];

  let pageNumber = 0;

  while (true) {
    const links = await scrapeListing(listPage, pageNumber);
    if (!links.length) {
      console.log("✅ No hay más páginas.");
      break;
    }

    const newLinks = links.filter(l => !visited.has(l));
    newLinks.forEach(l => visited.add(l));

    if (!newLinks.length) {
      pageNumber++;
      continue;
    }

    console.log(`➡ Procesando ${newLinks.length} publicaciones en paralelo...`);

    // Crear pool de workers (páginas reales)
    const workers: Page[] = [];
    for (let i = 0; i < MAX_CONCURRENCY; i++) {
      workers.push(await context.newPage());
    }

    const tasks = newLinks.map(async (link, i) => {
      const worker = workers[i % MAX_CONCURRENCY];
      const rows = await scrapeDetail(worker, link);
      results.push(...rows);
    });

    await Promise.allSettled(tasks);

    // Cerrar workers
    for (const w of workers) {
      await w.close();
    }

    pageNumber++;
  }

  const csvRows = [
    ["Título", "Fecha", "PDF", "URL"],
    ...results.map(r => [r.title, r.date, r.pdf, r.url])
  ];

  fs.writeFileSync(
    "iom_publicaciones_pdfs.csv",
    csvRows
      .map(row => row.map(f => `"${f.replace(/"/g, '""')}"`).join(","))
      .join("\n"),
    "utf-8"
  );

  console.log(`🎉 CSV generado con ${results.length} registros.`);

  await browser.close();
}

main();


