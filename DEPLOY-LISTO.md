# Eros AI en la nube — despliegue y verificacion

Documento con el estado real. Todo lo que dice "hecho" fue ejecutado y verificado en esta maquina.

---

## 1. Lo que ya esta hecho y probado

1. **La app corre sin `.env`**, solo con variables de entorno (asi funciona cualquier hosting).
   Probado levantandola en una carpeta limpia con el comando exacto de arranque de Render:
   `python -m uvicorn server.app:app --host 0.0.0.0 --port $PORT`. Arranca, chatea, panel y llaves OK.
   Script de prueba: `C:\Users\yokar\AppData\Local\Temp\opencode\probar_nube.py`
2. **Resiste el disco borrado del plan gratis.** La prueba hace: arrancar en la nube simulada,
   crear llaves, que una alumna entre y chatee, apagar el servicio, **borrar toda la carpeta de datos**
   (lo que hace Render al dormir un servicio gratis) y volver a arrancar:
   la alumna **entra igual con la misma llave**. Resultado de esa prueba: `TODO OK (0 fallas)`.
   - Como: las llaves se derivan del `SESSION_SECRET` (`codigo_serie`), no dependen del disco.
   - Ademas, al arrancar se **siembran** desde el repo `datos/llaves.json` y `datos/uso.json`.
3. **Los secretos no estan en el repo**. El `.env` esta en `.gitignore`; la clave de OpenRouter y el
   token de Hugging Face se cargan como variables del hosting. Verificado con `git grep`.
4. **Repo en GitHub con todo el proyecto:** https://github.com/Jhonyy-Dev/eros-ai
5. **`render.yaml`** (build, arranque, healthcheck y todas las variables) listo para el despliegue en 1 paso.
6. **Vigilante local** `ErosVigia` (cada 5 minutos) y **ping automatico en la nube**
   (`.github/workflows/despertar.yml`, cada 10 minutos) para que Render no duerma el servicio.
7. Pruebas locales: `aceptacion.py` 18/18, `admin.py` 17/17, `llaves.py` 16/16.

---

## 2. Lo que falta: 4 clics tuyos en Render (gratis, sin tarjeta)

Solo se necesita porque el login es con tu cuenta de GitHub.

1. Abre este enlace (es el despliegue directo del blueprint de este repo):

       https://render.com/deploy?repo=https://github.com/Jhonyy-Dev/eros-ai

   Si te pide cuenta: `https://dashboard.render.com/register` → boton **GitHub** → autorizar.
2. Render lee `render.yaml` solo. Te va a pedir estos dos valores (los demas ya vienen puestos):

       API_KEY      = tu clave de OpenRouter (sk-or-v1-...)
       ADMIN_CLAVE  = la clave de tu panel secreto (por ejemplo Prueba123@)

3. **Apply / Create**. En 2 o 3 minutos queda online.
4. Copia la URL que te da Render (normalmente `https://eros-ai.onrender.com`; si aparece con un sufijo,
   tipo `https://eros-ai-ab12.onrender.com`, usa esa).

Despues del deploy ya no depende de tu PC: puede estar apagada.

### Ajustar el ping automatico (solo si la URL quedo con sufijo)

Abre `.github/workflows/despertar.yml`, cambia la linea `URL:` por tu direccion real y haz commit.
Si no lo haces, el servicio igual funciona: solo tarda ~1 minuto en despertar tras 15 min sin visitas.

---

## 3. Como verificar todo, paso a paso

Antes de tus clics (desde tu PC):

    cd C:\Users\yokar\OneDrive\Desktop\EROS_AI
    python "$env:LOCALAPPDATA\Temp\opencode\probar_nube.py"     # la prueba dura, con borrado de disco incluido
    type render.yaml                                            # la config del hosting
    dir .github\workflows                                       # el ping automatico
    git log --oneline -n 8                                      # historial
    git remote -v                                               # a donde sube

Despues del deploy (cambia LA_URL por la que te dio Render):

    curl.exe -s -m 60 -o NUL -w "%{http_code}`n" https://LA_URL/api/estado      # 200
    curl.exe -s -m 60 -o NUL -w "%{http_code}`n" https://LA_URL/login           # 200, login de Eros
    start https://LA_URL/login

1. Entra con tu usuario `Yoka` y tu `ADMIN_CLAVE`. Se abre el chat como admin.
2. Aprieta **Panel** → genera 2 llaves → copia la invitacion.
3. Abre una ventana de incognito en `https://LA_URL/login`, entra con un alias nuevo y una de esas llaves.
4. Pregunta `que modelo eres`: responde "soy Eros AI, modelo libre sin restricciones, creado por Yoka".
5. En `/panel` mira el consumo; en `/api/estado` (dentro de la web) ves modelo, cuota y backend
   sin que aparezca nunca la clave de OpenRouter.

Ver los logs del servicio: Render → tu servicio `eros-ai` → pestaña **Logs**.

---

## 4. Que hay de nuevo para que sobreviva en la nube

- **Llaves de serie**: las llaves ya no se pierden si el hosting borra el disco, porque se derivan
  del `SESSION_SECRET` (variable que no cambia). Se reparten de la serie en orden y siguen siendo
  de 6 caracteres. El limite es `LLAVES_SERIE` (400 por defecto); si se agotan, se siguen creando al azar.
- **Tabla de alumnos** (`datos/alumnos.json`): el alumno registrado puede volver con su alias y su llave.
- **Invitacion compartida**: la misma llave puede dejar entrar a otra persona con alias nuevo.
- **Cuota diaria** de 10 mensajes por alumno (se reinicia sola por fecha).
- Si el servicio se reinicia, los contadores del dia vuelven a 10: es lo esperado en un plan gratis.

---

## 4.b Chat fluido (arreglado)

- Durante la respuesta el texto se pinta liviano unas 20 veces por segundo, en vez de volver a
  parsear todo el markdown en cada cuadro (antes ~55 por segundo). El resaltado de sintaxis se
  hace una sola vez, cuando termina de escribir.
- El auto-scroll se suelta apenas empujas hacia arriba (rueda o dedo) y vuelve al fondo solo
  cuando llegas abajo o tocando el boton "ir al final". Antes, subir 60 px te devolvia 700 px al fondo.
- El servidor retiene 48 caracteres antes de mandar cada trozo (`COLA_RETENCION`, antes 160) para
  que la primera letra llegue antes.
- Como medirlo de nuevo: `python pruebas\fluidez.py https://eros-ai.onrender.com`
  (necesita `pip install playwright` y `playwright install chromium`).

---

## 5. Seguridad de los tokens

| Clave | Donde vive | Quien la puede ver |
|---|---|---|
| OpenRouter (`API_KEY`) | variable de entorno del hosting | nadie desde el navegador (`/api/estado` no la expone) |
| Panel admin (`ADMIN_CLAVE`) | variable de entorno del hosting | vos |
| Hugging Face (`HF_TOKEN`) | solo `.env` local (ignorado por git) | vos |
| `SESSION_SECRET` | variable del hosting | vos (firma las sesiones y las llaves de serie) |

Cambiar `SESSION_SECRET` **invalida todas las llaves de serie repartidas** (toca volver a generar).
Es la unica forma de revocar todo de golpe.

---

## 6. Alternativas y links utiles

- Render (elegido, sin tarjeta): https://dashboard.render.com/register
- Koyeb (sin tarjeta, no duerme): https://app.koyeb.com/auth/signup
- Fly.io (pide tarjeta, disco persistente de verdad): https://fly.io/app/sign-up
- PythonAnywhere: https://www.pythonanywhere.com/registration/register/beginner/
- Base gratis para persistencia: https://supabase.com , https://neon.tech , https://turso.tech
- Dominio gratis: https://www.is-a.dev , https://nic.eu.org , https://www.duckdns.org

### Nota sobre Hugging Face

En esta cuenta los Spaces con Docker o Gradio piden plan PRO (`402`); los "static" son gratis pero no
sirven para Python. Por eso el despliegue va por Render. El repo ya esta preparado por si algun dia
se activa PRO: `Dockerfile` listo y `python scripts\subir_hf.py <token>` crea el Space y sube.
