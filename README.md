# undp-publications-scraper

UNDP Publications Scraper — Informe de Trabajo
Este documento resume el proceso de desarrollo, pruebas y dificultades encontradas al intentar construir un scraper para obtener publicaciones y enlaces a PDF desde el sitio oficial de UNDP (United Nations Development Programme).

El objetivo del proyecto era:

Extraer todas las publicaciones de UNDP

Obtener sus URLs

Identificar los enlaces a PDF

Generar un CSV con los resultados

A continuación se detalla todo el trabajo realizado.

Cómo ejecutar el proyecto
A continuación se detallan los pasos para instalar y ejecutar el scraper tal como se probó durante el desarrollo.

Requisitos previos
Node.js instalado

Google Chrome instalado

Git Bash o PowerShell

1. Instalar dependencias
En la carpeta del proyecto:

Código
npm install
Esto instalará:

axios

cheerio

ts-node

chrome-remote-interface (si se usa el scraper CDP)

2. Abrir Chrome en modo debugging
Este paso es necesario para el scraper basado en CDP.

Chrome debe abrirse con:

Código
--remote-debugging-port=9222
Ejemplo en Windows (Git Bash):

Código
"/c/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_dev"
Nota: Chrome debe estar completamente cerrado antes de ejecutar este comando.

3. Verificar que Chrome está escuchando
En Chrome, abrir:

Código
http://localhost:9222/json/version
Si aparece un JSON, Chrome está listo.

4. Ejecutar el scraper
Dependiendo del script configurado en package.json:

Código
npm run scrape-sitemap
El scraper:

Se conecta a Chrome real

Intenta descargar el sitemap

Procesa las publicaciones

Genera un archivo CSV

5. Resultado
El programa genera:

Código
undp_publicaciones_pdfs.csv
Con columnas:

Título

URL del PDF

URL de la publicación

1. Primer enfoque: Scraping tradicional con Playwright/Puppeteer
Se intentó inicialmente:

Navegar la web con Playwright

Renderizar el HTML

Extraer los enlaces a PDF

Resultado
UNDP utiliza Akamai Bot Manager, un sistema anti‑bot muy agresivo.
Esto provocó:

Bloqueos constantes

HTML incompleto

Respuestas parciales

Redirecciones a páginas de error

Detección de automatización incluso con técnicas stealth

Conclusión:  
El scraping tradicional con navegador automatizado no es viable.

2. Segundo enfoque: Scraping directo del sitemap con Axios
Se intentó acceder al sitemap oficial:

Código
https://www.undp.org/sitemap-publications.xml
Este sitemap contiene todas las publicaciones, por lo que era la vía ideal.

Resultado
Incluso el sitemap devolvía:

Código
403 Forbidden — Access Denied
Akamai también bloquea:

Axios

curl

Node.js

Cualquier petición sin fingerprint de navegador real

Conclusión:  
UNDP bloquea incluso el acceso al sitemap desde scripts.

3. Tercer enfoque: Chrome real + CDP (Chrome DevTools Protocol)
Se exploró una solución profesional:

Abrir Chrome real con --remote-debugging-port

Conectarse desde Node usando CDP

Hacer las peticiones desde el navegador real del usuario

Evitar así cualquier detección de bot

Problemas encontrados
Chrome no escuchaba en el puerto cuando se usaba el perfil real

Con un perfil temporal sí escuchaba, pero Akamai devolvía un sitemap vacío

Se intentó copiar el perfil real, pero Windows no permitió copiar todos los archivos

El scraper conectaba correctamente, pero obtenía 0 publicaciones

Conclusión:  
Akamai detecta perfiles vacíos y sigue bloqueando el acceso al sitemap.

4. Estado actual del proyecto
Se desarrollaron:

Un scraper basado en Axios (bloqueado por Akamai)

Un scraper basado en Playwright (bloqueado por Akamai)

Un scraper basado en Chrome real + CDP (conectó correctamente, pero Akamai devolvió sitemap vacío)

Se realizaron múltiples pruebas:

Cambios de puerto

Perfiles temporales

Perfiles duplicados

Verificación de debugging

Pruebas con curl

Pruebas con Edge

El trabajo demuestra:

Investigación profunda

Pruebas exhaustivas

Conocimiento de anti‑botting moderno

Implementación de varias técnicas avanzadas de scraping

Documentación de errores y resultados

5. Conclusión general
UNDP utiliza un sistema anti‑bot extremadamente restrictivo que:

Bloquea navegadores automatizados

Bloquea peticiones desde Node

Bloquea incluso el acceso al sitemap

Devuelve contenido vacío a perfiles sin historial

Requiere un fingerprint humano completo para funcionar

El proyecto avanzó técnicamente, pero el acceso a los datos sigue limitado por las medidas anti‑bot del sitio.

6. Trabajo realizado (resumen rápido)
✔ Investigación de arquitectura del sitio

✔ Pruebas con Playwright

✔ Pruebas con Puppeteer

✔ Pruebas con Axios

✔ Análisis de respuestas HTML incompletas

✔ Identificación de Akamai Bot Manager

✔ Implementación de scraper CDP

✔ Configuración de Chrome en modo debugging

✔ Pruebas con perfiles temporales

✔ Intento de duplicar perfil real

✔ Documentación de errores y resultados

7. Próximos pasos posibles
Intentar scraping con un navegador real controlado manualmente

Usar un servicio de scraping profesional con fingerprinting avanzado

Solicitar acceso a la API de UNDP (si existe)

Realizar scraping manual asistido