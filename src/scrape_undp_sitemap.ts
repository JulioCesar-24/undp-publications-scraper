import axios from "axios";
import * as cheerio from "cheerio";
import * as fs from "fs";

async function scrapeUNDP() {
  console.log("Descargando sitemap de publicaciones...");

  const sitemapUrl = "https://www.undp.org/sitemap-publications.xml";
  const sitemapXml = await axios.get(sitemapUrl).then(res => res.data);

  const urls = [...sitemapXml.matchAll(/<loc>(.*?)<\/loc>/g)].map(m => m[1]);

  console.log(`Publicaciones encontradas: ${urls.length}`);

  const rows: string[] = [];
  rows.push("Titulo,PDF,URL");

  for (const url of urls) {
    console.log("Procesando:", url);

    const html = await axios.get(url).then(res => res.data);
    const $ = cheerio.load(html);

    const title = $("h1").first().text().trim();

    const pdfs = $("a")
      .map((_, el) => $(el).attr("href"))
      .get()
      .filter(h => h && h.toLowerCase().endsWith(".pdf"));

    if (pdfs.length === 0) {
      rows.push(`"${title}",SIN_PDF,${url}`);
    } else {
      for (const pdf of pdfs) {
        rows.push(`"${title}",${pdf},${url}`);
      }
    }
  }

  fs.writeFileSync("undp_publicaciones_pdfs.csv", rows.join("\n"), "utf-8");

  console.log("CSV generado con éxito.");
}

scrapeUNDP();
