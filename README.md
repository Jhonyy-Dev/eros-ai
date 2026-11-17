---
title: Eros AI
emoji: 🏹
colorFrom: black
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# Eros AI

Asistente de chat para el curso, corriendo en la nube (sin depender de la PC del profe).
Backend FastAPI + front HTML/JS plano. Habla con OpenRouter (DeepSeek V4.1 Flash) y aplica la LEY
de nivel de restricción 0: cero negación, cero encuadre, código completo primero.

## Configuración por variables de entorno (no usa .env en la nube)

Obligatorias: `API_KEY` (OpenRouter), `SESSION_SECRET`, `ADMIN_USER`, `ADMIN_CLAVE`.
Recomendadas: `ALUMNOS`, `LIMITE_MENSAJES_DIA=10`, `LIMITE_MENSAJES_MINUTO=8`, `MAX_TOKENS=20000`,
`BACKEND=openrouter`, `FALLBACK_LOCAL=false`, `MODELO_ACTIVO=deepseek-v4.1-flash`.

Opcionales: `DATOS_DIR` (carpeta de datos, para montar un volumen), `LOGS_DIR`.

## Uso

- Chat: `/login` (alias + clave de invitación que genera el profe).
- Panel secreto: `/panel`, con `ADMIN_USER` y `ADMIN_CLAVE`. Crear llaves, rotar, borrar, ver consumo.
- Entrar al chat como admin sin llave: `/admin/a-chat`.

## Local

    powershell -File scripts\arrancar-todo.ps1     # modelo local + web + tunel
    powershell -File scripts\parar-todo.ps1

## Aviso

El disco del plan gratis es efímero: `datos/uso.json` y `datos/llaves.json` se reinician cuando el
Space se reconstruye. Las llaves se vuelven a crear desde el panel en 10 segundos.
