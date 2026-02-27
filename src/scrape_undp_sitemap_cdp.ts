import CDP from "chrome-remote-interface";
import * as cheerio from "cheerio";
import * as fs from "fs";

async function fetchWithChrome(url: string): Promise<string> {
  const client = await CDP({ port: 9223 });
  const { Network, Page } = client;

  await Network.enable();
  await Page.enable();

  return new Promise(async (resolve) => {
    let responseBody: string | null = null;

    Network.responseReceived(async (params: any) => {
      if (params.response.url === url) {
        const body = await Network.getResponseBody({
          requestId: params.requestId,
        });

        let text = body.body;

        if (body.base64Encoded) {
          text = Buffer.from(text, "base64").toString("utf-8");
        }

        responseBody = text;
      }
    });

    Page.loadEventFired(async () => {
      await client.close();
      resolve(responseBody || "");
    });

    await Page.navigate({ url });
  });
}


async function scrapeUNDP() {
  console.log("Descargando sitemap desde Chrome real...");

  const sitemapUrl = "https://www.w3.org/sitemap.xml";
  const xml = await fetchWithChrome(sitemapUrl);

  // Debug si viene vacío
  if (!xml || xml.trim().length < 20) {
    console.log("⚠ El sitemap vino vacío. Contenido recibido:");
    console.log(xml);
    return;
  }

  const urls = [...xml.matchAll(/<loc>(.*?)<\/loc>/g)].map((m) => m[1]);
  console.log(`Publicaciones encontradas: ${urls.length}`);

  const rows: string[] = [];
  rows.push("Titulo,PDF,URL");

  for (const url of urls) {
    console.log("Procesando:", url);

    const html = await fetchWithChrome(url);
    const $ = cheerio.load(html);

    const title = $("h1").first().text().trim();

    const pdfs = $("a")
      .map((_, el) => $(el).attr("href"))
      .get()
      .filter((h) => h && h.toLowerCase().endsWith(".pdf"));

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

