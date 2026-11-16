# parar-todo.ps1 - apaga chat publico, web y modelo
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
& 'D:\LocalAI\stop-web.ps1'
& 'D:\LocalAI\stop-ds9b.ps1'
"Eros apagado (modelo, web y tunel)"
