import { chromium } from "playwright";
import * as fs from "fs";

async function scrapeNASA() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  await page.goto("https://www.nasa.gov/news-release/", {
    waitUntil: "domcontentloaded"
  });

  await page.waitForSelector("article");

  const articles = await page.$$("article");
  console.log("Artículos encontrados:", articles.length);

  const rows: string[] = [];
  rows.push("Titulo,URL");

  for (const article of articles) {
    const title = await article.$eval("h3 a", el => el.textContent?.trim() || "");
    const link = await article.$eval("h3 a", el => (el as HTMLAnchorElement).href);

    rows.push(`"${title}",${link}`);
  }

  fs.writeFileSync("nasa_news.csv", rows.join("\n"), "utf-8");
  console.log("CSV generado con éxito.");

  await browser.close();
}

scrapeNASA();
