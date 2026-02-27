# undp-publications-scraper

1. Requisitos previos
Antes de ejecutar cualquier scraper necesitas:

Node.js (versión 16 o superior)

npm (incluido con Node)

Google Chrome instalado

Git Bash / PowerShell / CMD en Windows

 2. Instalar dependencias
En la carpeta raíz del proyecto:

bash
npm install
Esto instalará todas las librerías necesarias:

axios

cheerio

ts-node

playwright

chrome-remote-interface (solo para el scraper CDP)

otras dependencias del proyecto

 3. Estructura de scripts disponibles
En package.json tienes varios comandos que ejecutan distintos scrapers:

Script	Archivo ejecutado	Descripción
npm run start	src/scrape_undp.ts	Scraper base (Axios)
npm run scrape-sitemap	src/scrape_undp.ts	Scraper por sitemap (bloqueado por UNDP)
npm run scrape-html	src/scrape_undp_html.ts	Scraper HTML simple
npm run scrape-puppeteer	src/scrape_undp_puppeteer.ts	Scraper Puppeteer
npm run scrape-undp	src/scrape_undp_api.ts	Scraper API (endpoint no disponible)
npm run scrape-playwright	src/scrape_undp_playwright.ts	Scraper Playwright
npm run scrape-test	src/scrape_test.ts	Scraper de prueba (funciona siempre)
🧪 4. Ejecutar el scraper de prueba (recomendado)
Este scraper siempre funciona y sirve para verificar que tu entorno está bien configurado:

bash
npm run scrape-test
Genera:

Código
quotes.csv
 5. Ejecutar el scraper Playwright para UNDP
Este es el scraper principal que intenta obtener publicaciones de UNDP:

bash
npm run scrape-playwright
Este comando:

abre un navegador real con Playwright

navega por las páginas de publicaciones

intenta extraer títulos, URLs y PDFs

genera un archivo CSV con los resultados

Salida esperada:

Código
undp_publicaciones_pdfs.csv
Nota: UNDP utiliza Akamai Bot Manager, un sistema anti‑bot muy agresivo.
Dependiendo de la IP, cookies o fingerprint, puede devolver páginas vacías.

 6. Ejecutar el scraper CDP (Chrome real)
Este método usa tu navegador Chrome real para evitar bloqueos.

6.1. Abrir Chrome en modo debugging
Chrome debe estar completamente cerrado antes de ejecutar esto:

bash
"C:/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:/chrome_dev"
6.2. Verificar que Chrome está escuchando
Abre en tu navegador:

Código
http://localhost:9222/json/version
Si ves un JSON, Chrome está listo.

6.3. Ejecutar el scraper CDP
bash
npm run scrape-sitemap
 7. Archivos generados
Dependiendo del scraper, se generan:

undp_publicaciones_pdfs.csv

quotes.csv

otros CSV según el script ejecutado

 8. Limitaciones conocidas
UNDP utiliza Akamai Bot Manager, lo que provoca:

bloqueo de Axios

bloqueo de Playwright/Puppeteer

bloqueo de perfiles vacíos

bloqueo del sitemap

respuestas vacías o incompletas

detección de automatización

Por este motivo, algunos scrapers pueden devolver 0 resultados aunque el código sea correcto.

 9. Estado actual del proyecto
El proyecto incluye múltiples enfoques:

Scraping con Axios → bloqueado por Akamai

Scraping con Playwright → bloqueado parcialmente

Scraping con Puppeteer → bloqueado

Scraping con Chrome real vía CDP → conecta, pero recibe contenido vacío

Scraper de prueba → funciona correctamente

Esto demuestra que el entorno funciona, pero UNDP aplica restricciones severas.