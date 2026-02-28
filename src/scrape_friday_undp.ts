import axios from "axios";
import * as cheerio from "cheerio";
import * as fs from "fs";

const BASE: string = "https://www.undp.org";
const START_URL: string = `${BASE}/publications?combine=&sort_by=field_display_date_value`;

interface PublicationData {
  title: string;
  date: string;
  pdfLinks: string[];
  url: string;
}

async function getPublicationLinksFromPage(
  url: string
): Promise<{ links: string[]; nextPage: string | null }> {
  const { data } = await axios.get<string>(url);
  const $: cheerio.CheerioAPI = cheerio.load(data);

  const links: Set<string> = new Set();

  $("a[href^='/publications/']").each((_, el) => {
    const href = $(el).attr("href");
    if (href && !href.includes("?")) {
      links.add(BASE + href);
    }
  });

  return {
    links: Array.from(links),
    nextPage: getNextPage($)
  };
}

function getNextPage($: cheerio.CheerioAPI): string | null {
  const next = $("a[rel='next']").attr("href");
  return next ? BASE + next : null;
}

async function scrapePublication(url: string): Promise<PublicationData | null> {
  try {
    const { data } = await axios.get<string>(url);
    const $: cheerio.CheerioAPI = cheerio.load(data);

    const title: string = $("h1").first().text().trim();

    const date: string =
      $("time").first().text().trim() ||
      $("h1").first().next("div").text().trim();

    const pdfLinks: string[] = [];

    $("a[href$='.pdf']").each((_, el) => {
      let pdf = $(el).attr("href");

      if (pdf) {
        if (!pdf.startsWith("http")) {
          pdf = BASE + pdf;
        }
        pdfLinks.push(pdf);
      }
    });

    return {
      title,
      date,
      pdfLinks,
      url
    };
  } catch (error) {
    console.error("❌ Error en:", url);
    return null;
  }
}

async function main(): Promise<void> {
  let currentPage: string | null = START_URL;
  const allPublications: string[] = [];
  const visited: Set<string> = new Set();

  console.log("🔎 Extrayendo listado de publicaciones...");

  while (currentPage) {
    console.log("📄 Página:", currentPage);

    const { links, nextPage } = await getPublicationLinksFromPage(currentPage);

    links.forEach((link: string) => {
      if (!visited.has(link)) {
        visited.add(link);
        allPublications.push(link);
      }
    });

    currentPage = nextPage;
  }

  console.log(`📚 Total publicaciones encontradas: ${allPublications.length}`);

  const rows: string[][] = [["Título", "Fecha", "PDF", "URL"]];

  for (const link of allPublications) {
    console.log("➡ Procesando:", link);

    const data = await scrapePublication(link);

    if (data && data.pdfLinks.length > 0) {
      data.pdfLinks.forEach((pdf: string) => {
        rows.push([data.title, data.date, pdf, data.url]);
      });
    } else if (data) {
      rows.push([data.title, data.date, "", data.url]);
    }

    await new Promise<void>(resolve => setTimeout(resolve, 500));
  }

  fs.writeFileSync(
    "undp_publications.csv",
    rows
      .map(r =>
        r.map(field => `"${field.replace(/"/g, '""')}"`).join(",")
      )
      .join("\n")
  );

  console.log("✅ CSV generado: undp_publications.csv");
}

main();