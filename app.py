"""Site simples: cola a questão à esquerda, estrutura à direita.
Uso: python app.py  ->  http://localhost:8000
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

import joblib

from treinar import MODELO, analisar_todas

modelo = joblib.load(MODELO)

PAGINA = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Estruturador de Questões</title>
<style>
*{box-sizing:border-box}
body{font-family:system-ui,sans-serif;margin:0;background:#f4f5f7;color:#222}
header{padding:16px 24px;background:#1f3a5f;color:#fff}
h1{margin:0;font-size:20px}
main{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:16px 24px}
@media(max-width:800px){main{grid-template-columns:1fr}}
section{background:#fff;border-radius:8px;padding:16px;box-shadow:0 1px 3px #0002}
h2{margin:0 0 8px;font-size:15px;color:#1f3a5f}
textarea{width:100%;height:420px;padding:10px;font:14px/1.4 system-ui;border:1px solid #ccd;border-radius:6px;resize:vertical}
button{margin-top:10px;padding:10px 20px;background:#1f3a5f;color:#fff;border:0;border-radius:6px;font-size:15px;cursor:pointer}
button:hover{background:#2c5282}
.tag{display:inline-block;padding:3px 10px;border-radius:12px;font-size:13px;font-weight:600;color:#fff}
.sim{background:#2f855a}.nao{background:#c53030}
.campo{margin-top:14px}.campo b{display:block;font-size:12px;text-transform:uppercase;color:#667}
.campo div{white-space:pre-wrap;margin-top:4px}
ul{margin:4px 0 0;padding-left:20px}li{margin:3px 0}
details{margin-top:16px}pre{background:#f0f2f5;padding:10px;border-radius:6px;overflow:auto;font-size:12px}
.vazio{color:#889}
.item{margin-top:16px;padding-top:12px;border-top:1px solid #e3e6ea}
</style></head><body>
<header><h1>Estruturador de Questões de Concurso</h1></header>
<main>
<section><h2>Texto de entrada</h2>
<textarea id="entrada" placeholder="Cole aqui a questão (ou qualquer texto)..."></textarea>
<button onclick="enviar()">Estruturar</button></section>
<section><h2>Resultado</h2><div id="saida" class="vazio">O resultado aparece aqui.</div></section>
</main>
<script>
const esc=s=>s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
async function enviar(){
  const texto=document.getElementById('entrada').value.trim();
  const out=document.getElementById('saida');
  if(!texto){out.innerHTML='<span class="vazio">Digite um texto.</span>';return}
  const r=await fetch('/analisar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({texto})});
  const lista=await r.json();
  let h=lista.length>1?`<small>${lista.length} blocos encontrados</small>`:'';
  lista.forEach((d,i)=>{
    const pct=(d.probabilidade*100).toFixed(1)+'% de confiança de ser questão';
    h+=`<div class="item">`+(d.is_question
      ?`<span class="tag sim">${lista.length>1?'Questão '+(i+1)+': ':''}É questão de concurso</span> <small>${pct}</small>
        <div class="campo"><b>Cabeçalho</b><div>${esc(d.cabecalho)}</div></div>
        <div class="campo"><b>Enunciado</b><div>${esc(d.enunciado)||'<span class="vazio">Não encontrado</span>'}</div></div>
        <div class="campo"><b>Alternativas</b>${d.alternativas.length?'<ul>'+d.alternativas.map(a=>'<li>'+esc(a)+'</li>').join('')+'</ul>':'<div class="vazio">Nenhuma detectada</div>'}</div>`
      :`<span class="tag nao">Não é questão de concurso</span> <small>${pct}</small>`)+`</div>`;
  });
  h+=`<details><summary>JSON</summary><pre>${esc(JSON.stringify(lista,null,2))}</pre></details>`;
  out.innerHTML=h;
}
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _enviar(self, codigo, tipo, corpo):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        self._enviar(200, "text/html; charset=utf-8", PAGINA.encode("utf-8"))

    def do_POST(self):
        if self.path != "/analisar":
            return self._enviar(404, "text/plain", b"nao encontrado")
        tamanho = int(self.headers.get("Content-Length", 0))
        texto = json.loads(self.rfile.read(tamanho)).get("texto", "")
        resultado = analisar_todas(texto, modelo)
        self._enviar(200, "application/json; charset=utf-8",
                     json.dumps(resultado, ensure_ascii=False).encode("utf-8"))


if __name__ == "__main__":
    print("Abra http://localhost:8000")
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
