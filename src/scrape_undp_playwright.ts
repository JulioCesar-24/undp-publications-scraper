import { chromium } from "playwright-extra";
import stealth from "playwright-extra-plugin-stealth";
import * as fs from "fs";

chromium.use(stealth());

async function scrapeUNDP() {
  const browser = await chromium.launch({
    headless: false, // importante para evitar detección
  });

  const page = await browser.newPage();

  await page.goto("https://www.undp.org/publications", {
    waitUntil: "domcontentloaded",
  });

  // Esperar a que aparezcan artículos
  await page.waitForSelector("article", { timeout: 15000 });

  const articles = await page.$$("article");
  console.log("Artículos encontrados:", articles.length);

  const rows: string[] = [];
  rows.push("Titulo,PDF");

  for (const article of articles) {
    const title = await article.$eval("h3 a", el => el.textContent?.trim() || "");
    const link = await article.$eval("h3 a", el => (el as HTMLAnchorElement).href);

    const detail = await browser.newPage();
    await detail.goto(link, { waitUntil: "domcontentloaded" });

    const pdfs = await detail.$$eval("a", els =>
      els.map(a => (a as HTMLAnchorElement).href).filter(h => h.endsWith(".pdf"))
    );

    if (pdfs.length === 0) {
      rows.push(`${title},SIN_PDF`);
    } else {
      for (const pdf of pdfs) {
        rows.push(`${title},${pdf}`);
      }
    }

    await detail.close();
  }

  fs.writeFileSync("undp_publicaciones_pdfs.csv", rows.join("\n"), "utf-8");

  console.log("CSV generado con éxito.");
  await browser.close();
}

scrapeUNDP();



