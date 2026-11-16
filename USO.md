# Eros - motor local sin filtros + web con clave

## Que es
- Modelo local Qwen3.5-9B abliterated, entrenado por comportamiento (plantilla + reglas) para responder duro y concreto.
- Nombre publico: Eros. Habla español latino neutro, sin voseo.
- Web propia con clave compartida, cuota diaria y panel de uso. Tunel https de Cloudflare.
- Todo corre en tu maquina: el modelo en la GPU (llama-server 8099), la web en 127.0.0.1:8090.

## Comandos
- Modelo:  powershell -File D:\LocalAI\start-ds9b.ps1 -Modo eros     (detener: stop-ds9b.ps1)
- Web:     powershell -File D:\LocalAI\start-web.ps1                  (detener: stop-web.ps1, tambien mata el tunel)
- Tunel:   powershell -File D:\LocalAI\start-tunnel.ps1
- Panel:   http://127.0.0.1:8090/panel
- Estado:  http://127.0.0.1:8090/api/estado

Arranque automatico: "LocalAI DeepSeek9B.vbs", "LocalAI Web.vbs" y "LocalAI Tunel.vbs" en la carpeta Inicio.
La URL publica cambia si reinicias el tunel; se lee en el panel, en /api/estado y en logs\tunnel.log.

## Reglas de la prueba (web\config.json, luego reiniciar la web)
- limite_diario_por_ip: 20 peticiones por persona y por dia (se reinician a medianoche).
- tope_global_diario: 400 por dia en total.
- fecha_fin: 2026-11-20T23:59:59 (al pasar la fecha el chat queda cerrado).
- max_peticiones_en_vuelo_por_ip: 2.  max_tokens: 600 por defecto, hasta 800.
- clave_acceso: la compartida. upstream_api_key: la interna, el publico nunca la ve.
- Contadores en web\uso.json, con historico por dia.

## Modos del modelo (-Modo)
- eros (produccion): memoria de conversacion, primera linea con la respuesta, cero muletillas, datos duros,
  calculo con operacion escrita, español latino neutro, codigo completo y flags explicados, sin oponerse a nada.
- duro4, liberado, directo, pensante, raw: variantes anteriores para comparar.

## Web
- Blanco y negro, sin librerias, diseno moderno: tipografia sans, burbujas redondeadas, avatar, cajas de codigo
  con boton copiar, tarjetas de arranque, barra de cuota, barra lateral de conversaciones, tema invertido,
  responsive. Atajos: Enter envia, Shift+Enter salto, Esc detiene, Ctrl+K nueva conversacion.
- La clave va INCORPORADA en la pagina (el gateway la inyecta al servir el HTML): el usuario no escribe nada.
  El boton "copiar enlace" copia "url + clave" para compartir. "ver clave" la muestra.
- El limite se mide por IP real del visitante (cabecera CF-Connecting-IP detras del tunel).
- El historial de conversaciones queda en el navegador de cada persona, no en el servidor.
- El modelo no responde como consola: pregunta trivial = 1 a 3 lineas sin bloque de codigo; bloque ```lenguaje
  solo cuando el contenido es codigo real, un solo bloque por cosa, y codigo de una linea va en linea.

## Regla de oro de la GPU
-np x -c deben dejar mas de 1.5 GB de VRAM libre. Si la VRAM queda al borde, Windows baja memoria a RAM y el
rendimiento cae mas de 10x. Si el modelo arranca mientras otro llama-server no libero la VRAM, carga en CPU sin
avisar: start-ds9b.ps1 espera y verifica (campo vram_usada).
