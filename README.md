# Noticias con mirada católica

Archivos: `index.html` (la página), `update_news.py` (lee los feeds), `.github/workflows/update.yml` (corre cada hora).

## Puesta en marcha (gratis, ~5 minutos)
1. Crea un repositorio en GitHub y sube todo esto (incluida la carpeta `.github`).
2. Settings → Pages → Source: "Deploy from a branch" → `main` / root.
3. Pestaña Actions → "Actualizar noticias" → Run workflow. Crea `news.json`; desde ahí corre solo cada hora.
4. Revisa el "Estado de cada medio" al final de la página. Si un medio falla, corrige su dirección en la lista `SOURCES` de `update_news.py`.

Nota: GitHub puede retrasar unos minutos las tareas programadas.
