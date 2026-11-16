# Pasar Eros a un dominio fijo (gratis) — guía y opciones

Hoy todo corre en tu PC y la web sale por un túnel rápido de Cloudflare, por eso la URL cambia
cuando se cae el túnel. Estas son las formas de tener una URL que no cambie nunca, y dónde subir
el proyecto completo (front, back, datos). Todo con planes gratis y sin tarjeta salvo donde se aclara.

## Lo que ya está listo para desplegar

- `requirements.txt`, `Dockerfile` y `server/app.py` que respeta las variables `HOST` y `PORT`.
- La configuración se lee del `.env` (local) o de variables de entorno (nube), en ese orden.
- En la nube hay que definir: `API_KEY`, `SESSION_SECRET`, `ALUMNOS`, `LIMITE_MENSAJES_DIA=10`,
  `BACKEND=openrouter` y `FALLBACK_LOCAL=false` (el modelo local no es alcanzable desde afuera).

## Camino A — seguir en tu PC con URL fija (lo más rápido, 20 minutos)

1. Cuenta gratis en Tailscale (tailscale.com). Instalá Tailscale en tu PC e iniciá sesión.
2. En la terminal de Tailscale: `tailscale up` y después `tailscale funnel 8090`.
3. Te queda una URL fija tipo `https://tu-pc.tu-tailnet.ts.net` que no cambia nunca, apuntando a tu web.
   Requisito: la PC prendida. Alternativa equivalente: túnel con cuenta de Cloudflare + un dominio gratis
   (DuckDNS o eu.org).
4. Para el modelo local no hace falta abrir nada: el túnel publica solo la web (8090).

## Camino B — subir todo a la nube (la PC puede estar apagada)

Ninguno de estos necesita tarjeta:

- **Hugging Face Spaces** (recomendado para arrancar): sube el repo como Space con SDK Docker.
  Te da `https://usuario-nombre.hf.space`, fijo. Se duerme a las 48 h sin uso y despierta solo.
- **Render.com**: New → Web Service → repo de GitHub → Build `pip install -r requirements.txt` →
  Start `python -m uvicorn server.app:app --host 0.0.0.0 --port $PORT`. URL fija `algo.onrender.com`.
  Se duerme a los 15 min de inactividad y tarda 30-60 s en despertar.
- **Koyeb**: 1 servicio gratis, sin sleep, URL fija `algo.koyeb.app`.
- **Fly.io** (pide tarjeta): URL fija `algo.fly.dev` y además volúmenes persistentes, lo único que
  conserva `datos/uso.json` sin trucos.
- **PythonAnywhere**: siempre activo y URL fija, pero el plan gratis limita la salida a una lista blanca
  de sitios; si `api.openrouter.ai` no está, se pide por formulario.
- **Google Cloud Run** (pide tarjeta): escala a cero, URL fija, gratis dentro del cupo mensual.
- **Vercel**: hay que envolver FastAPI en `api/index.py` (ASGI). URL fija, disco efímero.

En todos: cargar las variables de entorno del apartado anterior y no subir el `.env`.

## Camino C — base de datos gratis (para no perder el registro de uso)

- **Supabase** (Postgres) o **Neon** (Postgres serverless): plan gratis sin tarjeta.
- **Turso** (SQLite distribuido) o **Upstash** (Redis): también gratis.
- Si no querés tocar código: Fly.io con volumen, o bajar `datos/uso.json` de vez en cuando.

## Dominio propio gratis (opcional)

- **eu.org**: dominio gratis de verdad (`tuclase.eu.org`), se pide y tarda días en aprobar.
- **is-a.dev** o **js.org**: subdominio gratis, se pide con un pull request en GitHub.
- **DuckDNS** o **FreeDNS (afraid.org)**: subdominio instantáneo, ideal para apuntar a un túnel.

## Pasos concretos del despliegue en la nube (Camino B)

1. Crear repo privado en GitHub y subir EROS_AI sin `.env`, `bin/`, `logs/` y `datos/`.
2. En el hosting elegido: nuevo servicio web desde el repo, detección por Dockerfile.
3. Cargar variables: `API_KEY`, `SESSION_SECRET`, `ALUMNOS`, `LIMITE_MENSAJES_DIA=10`,
   `MAX_TOKENS=20000`, `BACKEND=openrouter`, `FALLBACK_LOCAL=false`.
4. Deploy. Probar la URL del hosting con `/login` y un alumno de prueba.
5. Poner el dominio gratis (Camino C/D) apuntando al servicio.
6. Crear los alumnos con `python scripts/alumno.py nombre` y pasar el mensaje generado.

## Qué falta antes de subir

- Si querés conservar el uso entre reinicios, cambiar `datos/uso.json` por Postgres (Camino C).
- El modelo local queda como extra: si querés que la nube lo use, publicalo con Tailscale Funnel y
  poné `FALLBACK_LOCAL=true` y `LOCAL_URL=https://tu-pc.tu-tailnet.ts.net`.
