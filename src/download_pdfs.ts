import axios from "axios";
import * as fs from "fs";
import * as path from "path";

async function downloadPDFs() {
  const csvPath = "undp_publicaciones_pdfs.csv";

  if (!fs.existsSync(csvPath)) {
    console.error("El archivo CSV no existe. Ejecuta primero el scraper.");
    return;
  }

  const lines = fs.readFileSync(csvPath, "utf-8").split("\n").slice(1);

  const outputDir = "pdfs";
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir);
  }

  for (const line of lines) {
    if (!line.trim()) continue;

    const [title, url] = line.split(",");

    const safeName = title
      .replace(/[^a-zA-Z0-9-_ ]/g, "")
      .replace(/ /g, "_")
      .slice(0, 100); // evitar nombres demasiado largos

    const filePath = path.join(outputDir, `${safeName}.pdf`);

    try {
      console.log(`Descargando: ${title}`);

      const response = await axios.get(url, { responseType: "arraybuffer" });

      fs.writeFileSync(filePath, response.data);
    } catch (err) {
      console.error(`Error descargando ${title}:`, err);
    }
  }

  console.log("Descarga completada.");
}

downloadPDFs();
