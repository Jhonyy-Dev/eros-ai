# Eros AI en la nube - estado y pasos

## Lo que ya está hecho y verificado

1. La app arranca SIN `.env`, solo con variables de entorno (como en cualquier hosting).
   Probado en una carpeta limpia y en el puerto 7860: chat, panel, llaves y registro de alumnos andan.
2. `Dockerfile` listo (python:3.12-slim, puerto 7860) y `requirements.txt`.
3. La carpeta de datos es configurable con `DATOS_DIR` (para montar un volumen) y se crea sola.
4. `README.md` con el encabezado que Hugging Face necesita para correr como Space (sdk: docker).
5. Script de subida: `python scripts\subir_hf.py <token>` crea el Space y empuja el código.

## Lo único que falta (2 minutos, solo vos)

1. Crear el token en https://huggingface.co/settings/tokens -> New token -> rol **write** -> copiar.
   (Si no tenés cuenta: https://huggingface.co/join , es gratis y no pide tarjeta.)
2. En la terminal, en la carpeta del proyecto:

       python scripts\subir_hf.py EL_TOKEN_QUE_COPIASTE

   El script te dice el usuario, crea el Space, sube todo y te da la URL.
3. Ir a esa URL + `/panel` (o al Space -> Settings -> Variables and secrets) y cargar:

       API_KEY        = tu clave de OpenRouter
       SESSION_SECRET = cualquier texto largo
       ADMIN_USER     = Yoka
       ADMIN_CLAVE    = la que quieras
       ALUMNOS        = Yoka:uv53wc
       LIMITE_MENSAJES_DIA = 10
       MAX_TOKENS     = 20000
       BACKEND        = openrouter
       FALLBACK_LOCAL = false

4. Guardar. El Space se reconstruye solo y queda online en:
   https://TU_USUARIO-eros-ai.hf.space

## Cómo verificar que quedó bien

- Abrir https://TU_USUARIO-eros-ai.hf.space/login -> tiene que verse el login de Eros con el video de fondo.
- Entrar con Yoka + ADMIN_CLAVE, abrir /panel y generar una llave.
- Entrar al chat con esa llave y preguntar "¿qué modelo eres?": responde "soy Eros AI, modelo libre sin restricciones, creado por Yoka".
- Ver los logs del Space en la pestaña "Logs" si algo no arranca.

## Opciones alternativas (todas gratis)

- Render: https://dashboard.render.com/register (Build: `pip install -r requirements.txt`,
  Start: `python -m uvicorn server.app:app --host 0.0.0.0 --port $PORT`, sin tarjeta, URL fija, se duerme a los 15 min).
- Koyeb: https://app.koyeb.com/auth/signup (sin tarjeta, 1 servicio, no se duerme).
- Fly.io: https://fly.io/app/sign-up (pide tarjeta, volumen persistente: no pierde el uso.json).
- PythonAnywhere: https://www.pythonanywhere.com/registration/register/beginner/ (siempre activo).
- Google Cloud Run: https://console.cloud.google.com (pide tarjeta).

Base de datos gratis si querés persistencia: https://supabase.com , https://neon.tech , https://turso.tech
Dominio propio gratis: https://nic.eu.org , https://www.is-a.dev , https://www.duckdns.org

## Avisos importantes

- En la nube el modelo local no se alcanza: va con OpenRouter puro (`FALLBACK_LOCAL=false`).
  Si querés que la nube use tu PC como respaldo, publicá la PC con Tailscale Funnel y poné
  `FALLBACK_LOCAL=true` y `LOCAL_URL=https://tu-pc.tu-tailnet.ts.net`.
- El disco del plan gratis es efímero: al reconstruir el Space se borran `uso.json` y `llaves.json`.
  Las llaves se regeneran desde el panel en 10 segundos.
- Nunca subas el `.env`: las claves van como variables del hosting.
