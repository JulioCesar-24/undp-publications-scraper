import { chromium } from "playwright";
import * as fs from "fs";

async function scrapeTest() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  await page.goto("https://quotes.toscrape.com/", {
    waitUntil: "domcontentloaded"
  });

  await page.waitForSelector(".quote");

  const quotes = await page.$$(".quote");
  console.log("Frases encontradas:", quotes.length);

  const rows: string[] = [];
  rows.push("Quote,Author");

  for (const q of quotes) {
    const text = await q.$eval(".text", el => el.textContent?.trim() || "");
    const author = await q.$eval(".author", el => el.textContent?.trim() || "");
    rows.push(`"${text.replace(/"/g, '""')}",${author}`);
  }

  fs.writeFileSync("quotes.csv", rows.join("\n"), "utf-8");
  console.log("CSV generado con éxito.");

  await browser.close();
}

scrapeTest();
