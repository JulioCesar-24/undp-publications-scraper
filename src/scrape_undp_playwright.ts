import { chromium } from "playwright";
import * as fs from "fs";

async function scrapeUNDP() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  let pageNumber = 0;
  const rows: string[] = [];
  rows.push("Titulo,PDF,URL");

  while (true) {
    const url = `https://www.undp.org/search?search=&f%5B0%5D=type%3Apublication&page=${pageNumber}`;
    console.log(`Scrapeando página ${pageNumber}...`);

    await page.goto(url, { waitUntil: "domcontentloaded" });

    // Esperar a que aparezcan resultados
    try {
      await page.waitForSelector(".search-result", { timeout: 15000 });
    } catch {
      console.log("No hay más publicaciones. Fin.");
      break;
    }

    const cards = await page.$$(".search-result");
    console.log(`Publicaciones encontradas: ${cards.length}`);

    if (cards.length === 0) break;

    for (const card of cards) {
      const title = await card.$eval("h3.search-result__title a", el => el.textContent?.trim() || "");
      const link = await card.$eval("h3.search-result__title a", el => (el as HTMLAnchorElement).href);

      const detail = await browser.newPage();
      await detail.goto(link, { waitUntil: "domcontentloaded" });

      // Esperar un poco para que cargue el contenido
      await detail.waitForTimeout(2000);

      const pdfs = await detail.$$eval("a", els =>
        els
          .map(a => (a as HTMLAnchorElement).href)
          .filter(h => h.toLowerCase().endsWith(".pdf"))
      );

      if (pdfs.length === 0) {
        rows.push(`"${title}",SIN_PDF,${link}`);
      } else {
        for (const pdf of pdfs) {
          rows.push(`"${title}",${pdf},${link}`);
        }
      }

      await detail.close();
    }

    pageNumber++;
  }

  fs.writeFileSync("undp_publicaciones_pdfs.csv", rows.join("\n"), "utf-8");
  console.log("CSV generado con éxito.");

  await browser.close();
}

scrapeUNDP();







