import axios from "axios";
import * as fs from "fs";
import * as cheerio from "cheerio";

const BASE_URL = "https://www.undp.org/publications?page=";

async function scrapeUNDP_HTML() {
  let page = 0;
  const rows: string[] = [];
  rows.push("Titulo,PDF");

  while (true) {
    const url = `${BASE_URL}${page}`;
    console.log(`Scrapeando página ${page}...`);

    const response = await axios.get(url, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
      },
    });

    const html = response.data;
    const $ = cheerio.load(html);

    const items = $("article");

    if (items.length === 0) {
      console.log("No hay más resultados.");
      break;
    }

    items.each((_, el) => {
      const title = $(el).find("h3 a").text().trim().replace(/,/g, " ");

      // Buscar PDFs dentro del artículo
      $(el)
        .find("a")
        .each((_, link) => {
          const href = $(link).attr("href");
          if (href && href.endsWith(".pdf")) {
            const pdfUrl = href.startsWith("http")
              ? href
              : "https://www.undp.org" + href;

            rows.push(`${title},${pdfUrl}`);
          }
        });
    });

    page++;
  }

  fs.writeFileSync("undp_publicaciones_pdfs.csv", rows.join("\n"), "utf-8");
  console.log("CSV generado con éxito.");
}

scrapeUNDP_HTML();
