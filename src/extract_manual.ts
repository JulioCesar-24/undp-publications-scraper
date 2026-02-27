import CDP from "chrome-remote-interface";
import * as fs from "fs";
import * as cheerio from "cheerio";

async function extractFromTab(target: any, client: any) {
  const { Runtime } = client;

  const result = await Runtime.evaluate({
    expression: "document.documentElement.outerHTML",
    returnByValue: true
  });

  const html = result.result.value;
  const $ = cheerio.load(html);

  const title = $("h1.page-title").text().trim();
  const date = $("div.field--name-field-display-date").text().trim();
  const pdf = $("a.button--download").attr("href") || "";

  return {
    url: target.url,
    title,
    date,
    pdf
  };
}

async function main() {
  const client = await CDP({ port: 9222 });
  const { Target } = client;

  const targets = await Target.getTargets();

  const pages = targets.targetInfos.filter(
    (t: any) =>
      t.type === "page" &&
      t.url.includes("undp.org") &&
      !t.url.includes("publications?")
  );

  const rows = [["Título", "Fecha", "PDF", "URL"]];

  for (const target of pages) {
    const tab = await CDP({ target });
    const data = await extractFromTab(target, tab);
    rows.push([data.title, data.date, data.pdf, data.url]);
    await tab.close();
  }

  fs.writeFileSync("undp_manual_extract.csv", rows.map(r => r.join(",")).join("\n"));
  console.log("CSV generado: undp_manual_extract.csv");

  await client.close();
}

main();
