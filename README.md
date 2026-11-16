# Eros

Asistente de chat para el curso. Backend FastAPI + front HTML/JS plano (sin bundler).
Los alumnos entran con nombre y código, conversan en la web y el servidor decide con qué
modelo responder: OpenRouter en la nube y, si falla, el modelo local calibrado en la GPU.

## Arrancar / apagar

    powershell -ExecutionPolicy Bypass -File scripts\arrancar-todo.ps1    # modelo local + web + tunel
    powershell -ExecutionPolicy Bypass -File scripts\parar-todo.ps1       # apaga todo
    powershell -ExecutionPolicy Bypass -File scripts\modo-solo-chat.ps1   # sin voz: Eros completo (20 slots, 131k)
    powershell -ExecutionPolicy Bypass -File scripts\modo-voz.ps1         # con la voz de OpenBot: Eros compacto

Autostart: tres accesos en la carpeta Inicio (`Eros Modelo.vbs`, `Eros Web.vbs`, `Eros Tunel.vbs`).
La URL pública del túnel se imprime al arrancar, queda en `url_publica.txt`, en `/api/estado` y en el panel.

## Panel secreto del profe y creación de alumnos

El panel vive en `/panel` y está protegido por `ADMIN_CLAVE` (cookie aparte de la de los alumnos):
los alumnos que entren a `/panel` ven la pantalla de clave y no pueden tocar nada.

Desde el panel, con un botón:

- **Crear alumno**: nombre o alias + código aleatorio de 6 caracteres.
- **Crear 10 de golpe**: por si arrancás con un grupo completo (genera alumno01..alumno10).
- **rotar código**: cambia el código de ese alumno. El viejo muere al instante, así el que lo filtró
  no entra más y el alumno vuelve a entrar con el código nuevo que le pases.
- **borrar**: lo saca del sistema. Si quiere volver, se le crea un código nuevo.
- **copiar invitación**: copia el mensaje listo (enlace + nombre + código) para pegar en el grupo.
- **Copiar todos los códigos**: el listado completo de una vez.

Los códigos se guardan en `.env` (línea `ALUMNOS=`) y aplican al instante, sin reiniciar la web.
También se puede hacer por consola: `python scripts\alumno.py ana` (crea), `--lista`, `--borrar ana`.

Si cambiás la clave del panel, editá `ADMIN_CLAVE` en el `.env` y reiniciá la web.

## Variables del .env

| variable | para qué | por defecto |
|---|---|---|
| `API_KEY` | clave de OpenRouter. Solo la ve el servidor | — |
| `MODELO_ACTIVO` | id del modelo en `config/models.py` | deepseek-v4.1-flash |
| `BACKEND` | openrouter o local | openrouter |
| `FALLBACK_LOCAL` | si OpenRouter falla, sigue con el modelo local | true |
| `MAX_TOKENS` | tope de salida por respuesta | 4096 |
| `MAX_MENSAJES_CONTEXTO` / `MAX_TOKENS_CONTEXTO` | historial enviado | 20 / 32000 |
| `LIMITE_MENSAJES_DIA` / `LIMITE_MENSAJES_MINUTO` | límites por alumno | 10 / 5 |
| `ALUMNOS` | nombre:codigo separado por comas | profe:eros2026 |
| `SESSION_SECRET` | firma de la cookie | — |
| `PUERTO` | puerto de la web | 8090 |
| `LOCAL_URL` / `LOCAL_KEY` | motor local (llama-server) | 127.0.0.1:8099 |
| `ENABLE_STUDENT_API_KEYS` | fase futura de API por alumno | false |

La `API_KEY` nunca se manda al navegador: el front llama a `/api/chat` y el servidor a OpenRouter.
`.env` está en `.gitignore`; `.env.example` tiene las mismas variables vacías.

## Estructura

    server/    app.py (gateway), index.html (chat oscuro), login.html, panel.html
    motor/     llm.py: único lugar donde se llama al modelo (streaming, reintento, respaldo)
    config/    models.py (lista de modelos), personas/eros.txt (carácter de Eros), ds9b-*.jinja (motor local)
    scripts/   arranque, parada, túnel, modos
    datos/     uso.json (mensajes y tokens por alumno)
    bin/       llama-server.exe, cloudflared.exe y sus dlls
    pruebas/   aceptacion.py (17 pruebas), limites.py (minuto y día)

El modelo local está calibrado a mano (`config/ds9b-eros.jinja` + persona): no se retoca para
OpenRouter, se replica su comportamiento con la persona en `config/personas/eros.txt`.

## Modelos

`config/models.py` tiene la lista. Hoy hay UN modelo para alumnos: DeepSeek V4.1 Flash
(`deepseek/deepseek-v4.1-flash-1017`, proveedor deepinfra en fp8, con respaldo automático).
Agregar otro es sumar una entrada y cambiar `MODELO_ACTIVO`.

## Pendiente para la próxima fase

- API keys por alumno y endpoint `/v1` compatible con OpenAI (hoy `ENABLE_STUDENT_API_KEYS=false`).
  `motor/llm.py` ya es la capa única, así que se puede poner delante LiteLLM sin tocar el chat.
- Selector de modelos en el front (cuando haya más de uno).
- Hosting para que la URL no cambie: el túnel rápido de Cloudflare da una URL nueva en cada arranque.
