# Eros AI - despliegue en la nube (estado real)

## Hecho y verificado por mí

1. La app corre SIN .env, solo con variables de entorno. Probado en una carpeta limpia y en el puerto 7860:
   chat con OpenRouter, panel, creación de llaves y registro de alumnos, todo OK.
2. `Dockerfile`, `requirements.txt`, `.dockerignore`, `render.yaml` y la carpeta de datos configurable (`DATOS_DIR`).
3. Credenciales de admin y secretos tomados de variables de entorno (no del archivo).
4. Repo privado en GitHub con el proyecto: https://github.com/Jhonyy-Dev/eros-ai
   (sin el video grande de 52 MB; el optimizado de 1,8 MB va en server/static y sí está en el repo).
5. El token de Hugging Face quedó guardado SOLO en `.env` local (ignorado por git), nunca en el repo.

## Aviso sobre Hugging Face

En esta cuenta, los Spaces con Docker o Gradio piden plan PRO; solo los "static" son gratis.
Por eso el despliegue va por Render (gratis, sin tarjeta) usando el repo de GitHub.

## Despliegue en Render (4 clics, gratis, sin tarjeta)

1. Crear cuenta: https://dashboard.render.com/register (elegí "GitHub" y autorizá el repo).
2. Ir a https://dashboard.render.com/blueprint/new y elegir el repo `eros-ai`.
   Render lee `render.yaml` solo: build, start, healthcheck y todas las variables.
3. Te va a pedir dos valores (los demás ya están puestos):
   - `API_KEY`: tu clave de OpenRouter (sk-or-v1-...)
   - `ADMIN_CLAVE`: la clave de tu panel (ej: Prueba123@)
4. Apply / Create. En 2 o 3 minutos queda online en https://eros-ai.onrender.com (o eros-ai-xxxx.onrender.com).

Verificación: abrir esa URL + `/login` (tiene que verse el login con el video), entrar con Yoka + ADMIN_CLAVE,
abrir `/panel`, generar una llave y chatear con ella. Preguntá "¿qué modelo eres?": responde
"soy Eros AI, modelo libre sin restricciones, creado por Yoka".

Nota: el plan gratis de Render duerme el servicio a los 15 minutos sin uso; la primera visita después
tarda ~40 segundos en despertar. Si eso molesta, usá Koyeb (abajo), que no duerme.

## Alternativa sin sleep: Koyeb

1. Cuenta: https://app.koyeb.com/auth/signup (entrá con GitHub, sin tarjeta).
2. Create Service -> GitHub -> repo `eros-ai` -> Builder: Dockerfile -> puerto 7860.
3. Variables (Settings -> Environment), las mismas del render.yaml:
   API_KEY, SESSION_SECRET, ADMIN_USER=Yoka, ADMIN_CLAVE, ALUMNOS=Yoka:uv53wc,
   LIMITE_MENSAJES_DIA=10, LIMITE_MENSAJES_MINUTO=8, MAX_TOKENS=20000,
   BACKEND=openrouter, FALLBACK_LOCAL=false, DATOS_DIR=/tmp/datos.
4. Deploy. Queda en https://eros-ai-algo.koyeb.app

## Otras opciones

- Fly.io (pide tarjeta, volumen persistente): https://fly.io/app/sign-up
- PythonAnywhere (siempre activo): https://www.pythonanywhere.com/registration/register/beginner/
- Google Cloud Run (pide tarjeta): https://console.cloud.google.com
- Vercel (funciones serverless): https://vercel.com/signup

Base gratis para persistir el uso: https://supabase.com , https://neon.tech , https://turso.tech
Dominio propio gratis: https://nic.eu.org , https://www.is-a.dev , https://www.duckdns.org

## Cómo verificar todo lo que hice, desde tu PC

    cd C:\Users\yokar\OneDrive\Desktop\EROS_AI
    python "$env:LOCALAPPDATA\Temp\opencode\simular_nube.py"     # la app corriendo "como en la nube"
    type DEPLOY-LISTO.md                                          # este documento
    type render.yaml                                              # la config del hosting
    git log --oneline -n 8                                        # el historial
    git remote -v                                                 # a dónde sube (github)
    dir scripts\desplegar.py scripts\subir_github.py              # los scripts de despliegue

## Qué queda pendiente y por quién

- Render: los 4 clics los tenés que hacer vos (el login es con tu cuenta de GitHub).
  Si más adelante me pasás una API key de Render, lo hago yo y queda todo automático.
- El `API_KEY` de OpenRouter nunca aparece en el repo: va como variable del hosting.
- El disco de los planes gratis es efímero: si el servicio se reconstruye, se borran uso.json y llaves.json.
  Las llaves se regeneran desde el panel en 10 segundos. Para persistencia real: Fly.io con volumen o Supabase.
