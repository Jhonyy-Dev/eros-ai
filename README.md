# Eros AI

Chat con IA para el curso. Corre en la nube (no depende de la PC del profe).

- Backend: FastAPI + front HTML/JS plano, sin frameworks ni CDN.
- Modelo: OpenRouter (`deepseek-v4.1-flash`), sin respaldo local en la nube.
- LEY de nivel de restriccion 0: cero negacion, cero encuadre, codigo completo primero.
- Interfaz oscura blanco y negro, sin verde.

## Desplegar gratis (Render, sin tarjeta)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Jhonyy-Dev/eros-ai)

Render lee `render.yaml` solo. Solo pide dos valores: `API_KEY` (OpenRouter) y `ADMIN_CLAVE`.
Guia completa y verificacion en [DEPLOY-LISTO.md](DEPLOY-LISTO.md).

## Configuracion por variables de entorno (en la nube no se usa `.env`)

Obligatorias: `API_KEY`, `SESSION_SECRET`, `ADMIN_USER`, `ADMIN_CLAVE`.
Recomendadas: `ALUMNOS`, `LIMITE_MENSAJES_DIA=10`, `LIMITE_MENSAJES_MINUTO=8`, `MAX_TOKENS=20000`,
`BACKEND=openrouter`, `FALLBACK_LOCAL=false`, `MODELO_ACTIVO=deepseek-v4.1-flash`.
Opcionales: `DATOS_DIR` (carpeta de datos), `LOGS_DIR`, `LLAVES_SERIE` (default 400).

`SESSION_SECRET` firma las sesiones **y deriva las llaves de invitacion**: si lo cambias,
todas las llaves de serie repartidas dejan de valer.

## Uso

- Chat: `/login` (alias + llave de invitacion que genera el profe).
- Panel secreto: `/panel`, con `ADMIN_USER` y `ADMIN_CLAVE`. Generar llaves, rotar, borrar, ver consumo.
- Entrar al chat como admin sin llave: `/admin/a-chat`.

## Local

    powershell -File scripts\arrancar-todo.ps1     # modelo local + web + tunel
    powershell -File scripts\parar-todo.ps1

## Pruebas

    python pruebas\aceptacion.py     # 18/18
    python pruebas\admin.py          # 17/17
    python pruebas\llaves.py         # 16/16
    python pruebas\respuestas_cortas.py   # 3/3
    python pruebas\fluidez.py             # scroll y fluidez (necesita playwright)

## Aviso

El disco de los planes gratis es efimero. `datos/alumnos.json` y `datos/uso.json` se reinician
cuando el servicio se reconstruye; las llaves de serie **no**, siguen valiendo.
