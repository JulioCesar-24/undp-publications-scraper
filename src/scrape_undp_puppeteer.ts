import puppeteer from "puppeteer-extra";
import StealthPlugin from "puppeteer-extra-plugin-stealth";
import * as fs from "fs";

puppeteer.use(StealthPlugin());

async function scrapeUNDP() {
  const browser = await puppeteer.launch({
    headless: false, // visible para evitar detección
    defaultViewport: null,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-blink-features=AutomationControlled",
    ],
  });

  const page = await browser.newPage();

  console.log("Cargando página de publicaciones...");
  await page.goto("https://www.undp.org/publications", {
    waitUntil: "networkidle2",
  });

  // Scroll lento para cargar contenido
  await autoScroll(page);

  // Esperar artículos
  await page.waitForSelector("article", { timeout: 15000 });

  const articles = await page.$$("article");
  console.log("Artículos encontrados:", articles.length);

  // DEBUG: ver el HTML del primer artículo
if (articles.length > 0) {
  const html = await page.evaluate(el => el.innerHTML, articles[0]);
  console.log("Primer artículo HTML:\n", html);
}

  
  const rows: string[] = [];
  rows.push("Titulo,PDF");

  for (const article of articles) {
    const title = await article.$eval("h3 a", el => el.textContent?.trim() || "");
    const link = await article.$eval("h3 a", el => (el as HTMLAnchorElement).href);

    console.log("Entrando en:", title);

    const detail = await browser.newPage();
    await detail.goto(link, { waitUntil: "networkidle2" });

    await autoScroll(detail);

    const pdfs = await detail.$$eval("a", els =>
      els
        .map(a => (a as HTMLAnchorElement).href)
        .filter(h => h.toLowerCase().endsWith(".pdf"))
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

async function autoScroll(page: any) {
  await page.evaluate(async () => {
    await new Promise<void>((resolve) => {
      let totalHeight = 0;
      const distance = 300;

      const timer = setInterval(() => {
        const scrollHeight = document.body.scrollHeight;
        window.scrollBy(0, distance);
        totalHeight += distance;

        if (totalHeight >= scrollHeight - window.innerHeight) {
          clearInterval(timer);
          resolve();
        }
      }, 200);
    });
  });
}

scrapeUNDP();
