import axios from "axios";
import * as fs from "fs";

const BASE_API = "https://www.undp.org/api/publications?page=";
const BASE_URL = "https://www.undp.org";

interface FileInfo {
  uri: { url: string };
}

interface Publication {
  title: string;
  field_document?: FileInfo[];
  field_publication_file?: FileInfo[];
}

async function scrapeUNDP() {
  let page = 0;
  const rows: string[] = [];
  rows.push("Titulo,PDF");

  while (true) {
    console.log(`Scrapeando página ${page}...`);

    const url = `${BASE_API}${page}`;
    const response = await axios.get(url, {
  headers: {
    "User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.undp.org/publications",
    "Origin": "https://www.undp.org",
  }
});


    const data = response.data;

    if (!data.data || data.data.length === 0) {
      console.log("No hay más resultados.");
      break;
    }

    for (const item of data.data as Publication[]) {
      const title = item.title.replace(/,/g, " ");

      const pdfFields = ["field_document", "field_publication_file"] as const;

      for (const field of pdfFields) {
        const files = item[field];
        if (files) {
          for (const file of files) {
            const pdfUrl = BASE_URL + file.uri.url;
            rows.push(`${title},${pdfUrl}`);
          }
        }
      }
    }

    page++;
  }

  fs.writeFileSync("undp_publicaciones_pdfs.csv", rows.join("\n"), "utf-8");
  console.log("CSV generado con éxito.");
}

scrapeUNDP();
