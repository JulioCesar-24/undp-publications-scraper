import fetch from "node-fetch";
import * as fs from "fs";

async function fetchAllPublications() {
  let url = "https://www.undp.org/jsonapi/node/publication?page[limit]=50";
  const rows = ["Titulo,PDF,URL"];

  while (url) {
    console.log("Descargando:", url);

    const res = await fetch(url);
    const json: any = await res.json(); // 👈 Tipado flexible

    for (const item of json.data) {
      const title = item.attributes.title;
      const path = "https://www.undp.org" + item.attributes.path.alias;

      // Obtener PDFs asociados
      const detailUrl = `https://www.undp.org/jsonapi/node/publication/${item.id}?include=field_document`;
      const detailRes = await fetch(detailUrl);
      const detailJson: any = await detailRes.json(); // 👈 Aquí está la corrección

      const included = detailJson.included || [];
      const pdfs = included
        .filter((i: any) => i.attributes?.uri?.url?.endsWith(".pdf"))
        .map((i: any) => i.attributes.uri.url);

      if (pdfs.length === 0) {
        rows.push(`"${title}",SIN_PDF,${path}`);
      } else {
        for (const pdf of pdfs) {
          rows.push(`"${title}",${pdf},${path}`);
        }
      }
    }

    // Paginación
    url = json.links?.next?.href || null;
  }

  fs.writeFileSync("undp_publicaciones_pdfs.csv", rows.join("\n"), "utf-8");
  console.log("CSV generado con éxito.");
}

fetchAllPublications();

