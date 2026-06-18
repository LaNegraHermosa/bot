import bcrypt
import secrets
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional

from .config import settings

security = HTTPBasic()

_ADMIN_PASSWORD_HASH = bcrypt.hashpw(settings.ADMIN_PASSWORD.encode(), bcrypt.gensalt()) if settings.ADMIN_PASSWORD else b""

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if not settings.ADMIN_USER or not settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=503, detail="Admin not configured. Set ADMIN_USER and ADMIN_PASSWORD env vars.")
    user_ok = secrets.compare_digest(credentials.username, settings.ADMIN_USER)
    pass_ok = bcrypt.checkpw(credentials.password.encode(), _ADMIN_PASSWORD_HASH)
    if not (user_ok and pass_ok):
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Basic"})
    return True

docs_enabled = settings.ENV == "development"
app = FastAPI(title="Bot Tienda", docs_url="/docs" if docs_enabled else None, redoc_url="/redoc" if docs_enabled else None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)

class WebMessage(BaseModel):
    message: str
    user_id: str
    platform: str = "web"

# ── WhatsApp webhook (solo si TWILIO configurado) ──
if settings.WHATSAPP_ENABLED:
    from twilio.twiml.messaging_response import MessagingResponse
    from .handlers.whatsapp import whatsapp_handler

    @app.post("/whatsapp/webhook")
    async def whatsapp_webhook(request: Request):
        try:
            form = await request.form()
            phone = form.get("From", "").replace("whatsapp:", "")
            text = form.get("Body", "")
            resp = await whatsapp_handler.handle_message(phone, text)
            twiml = MessagingResponse()
            twiml.message(resp)
            return Response(content=str(twiml), media_type="application/xml")
        except Exception:
            twiml = MessagingResponse()
            twiml.message("Error interno.")
            return Response(content=str(twiml), media_type="application/xml")

# ── Web chat (usa WhatsAppHandler, funciona sin Twilio) ──
from .handlers.whatsapp import whatsapp_handler

@app.post("/web/chat")
async def web_chat(data: WebMessage):
    try:
        resp = await whatsapp_handler.handle_message(data.user_id, data.message)
        return {"response": resp}
    except Exception:
        raise HTTPException(status_code=500, detail="Error")

# ── API pública ──
@app.get("/api/products")
async def get_products(category: Optional[str] = None):
    from .services.database import DatabaseService
    try:
        return [p.model_dump() for p in DatabaseService.get_products(category=category)]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Admin Dashboard ──
ADMIN_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Panel Admin</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;color:#333}
        .header{background:#1a1a2e;color:#fff;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center}
        .container{max-width:1200px;margin:2rem auto;padding:0 1rem}
        .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:2rem}
        .stat-card{background:#fff;padding:1.5rem;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,.1)}
        .stat-card h3{font-size:.875rem;color:#666;margin-bottom:.5rem}
        .stat-card .value{font-size:2rem;font-weight:700;color:#1a1a2e}
        .card{background:#fff;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,.1);margin-bottom:1.5rem;overflow:hidden}
        .card-header{padding:1rem 1.5rem;border-bottom:1px solid #eee;font-weight:600;display:flex;justify-content:space-between}
        .card-body{padding:1.5rem;overflow-x:auto}
        table{width:100%;border-collapse:collapse}
        th,td{text-align:left;padding:.75rem;border-bottom:1px solid #eee;font-size:.875rem}
        th{color:#666;font-weight:600}
        .badge{display:inline-block;padding:.25rem .5rem;border-radius:4px;font-size:.75rem;font-weight:600}
        .badge-pending{background:#fff3cd;color:#856404}
        .badge-confirmed{background:#cce5ff;color:#004085}
        .badge-preparing,.badge-ready,.badge-delivered{background:#d4edda;color:#155724}
        .badge-cancelled{background:#f8d7da;color:#721c24}
        .btn{display:inline-block;padding:.375rem .75rem;border-radius:4px;border:none;cursor:pointer;font-size:.8rem}
        .btn-primary{background:#1a1a2e;color:#fff}
        .loading{text-align:center;padding:2rem;color:#666}
        .error{color:#721c24;background:#f8d7da;padding:1rem;border-radius:4px}
        select{padding:.25rem;border-radius:4px;border:1px solid #ccc}
    </style>
</head>
<body>
<div class="header"><h1>📊 Panel Admin</h1><span id="refresh-time"></span></div>
<div class="container">
    <div class="stats" id="stats"></div>
    <div class="card">
        <div class="card-header"><span>📦 Órdenes</span><button class="btn btn-primary" onclick="loadData()">↻</button></div>
        <div class="card-body" id="orders-table"><div class="loading">Cargando...</div></div>
    </div>
    <div class="card">
        <div class="card-header"><span>🛍 Productos</span></div>
        <div class="card-body" id="products-table"><div class="loading">Cargando...</div></div>
    </div>
</div>
<script>
async function loadData(){try{
const[s,r,p]=await Promise.all([fetch('/admin/api/stats'),fetch('/admin/api/orders'),fetch('/admin/api/products')]);
if(s.status===401||s.status===503){document.getElementById('orders-table').innerHTML='<div class=\\"error\\">No autorizado o no configurado</div>';return}
const stats=await s.json(),orders=await r.json(),products=await p.json();
document.getElementById('refresh-time').textContent=new Date().toLocaleString();
document.getElementById('stats').innerHTML=`
<div class=\\"stat-card\\"><h3>Órdenes</h3><div class=\\"value\\">${stats.total_orders}</div></div>
<div class=\\"stat-card\\"><h3>Pendientes</h3><div class=\\"value\\">${stats.pending_orders}</div></div>
<div class=\\"stat-card\\"><h3>Clientes</h3><div class=\\"value\\">${stats.total_customers}</div></div>
<div class=\\"stat-card\\"><h3>Productos</h3><div class=\\"value\\">${stats.total_products}</div></div>
<div class=\\"stat-card\\"><h3>Ingresos</h3><div class=\\"value\\">$${stats.total_revenue}</div></div>`;
var h='<table><thead><tr><th>ID</th><th>Cliente</th><th>Total</th><th>Estado</th><th>Fecha</th></tr></thead><tbody>';
orders.forEach(o=>{h+=`<tr><td>#${o.id}</td><td>${o.customer_name||'—'}</td><td>$${o.total}</td><td><span class=\\"badge badge-${o.status}\\">${o.status}</span></td><td>${new Date(o.created_at).toLocaleDateString()}</td></tr>`});
document.getElementById('orders-table').innerHTML=h+'</tbody></table>';
h='<table><thead><tr><th>ID</th><th>Nombre</th><th>Precio</th><th>Stock</th><th>Categoría</th></tr></thead><tbody>';
products.forEach(p=>{h+=`<tr><td>${p.id}</td><td>${p.name}</td><td>$${p.price}</td><td>${p.stock}</td><td>${p.category||'—'}</td></tr>`});
document.getElementById('products-table').innerHTML=h+'</tbody></table>';
}catch(e){document.getElementById('orders-table').innerHTML='<div class=\\"error\\">Error de conexión</div>'}}
loadData();setInterval(loadData,30000);
</script>
</body>
</html>"""

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(_=Depends(verify_admin)):
    return ADMIN_HTML

@app.get("/admin/api/stats")
async def admin_stats(_=Depends(verify_admin)):
    from .services.database import DatabaseService
    return DatabaseService.get_admin_stats()

@app.get("/admin/api/orders")
async def admin_orders(_=Depends(verify_admin)):
    from .services.database import DatabaseService
    return DatabaseService.get_all_orders()

@app.get("/admin/api/products")
async def admin_products(_=Depends(verify_admin)):
    from .services.database import DatabaseService
    return [p.model_dump() for p in DatabaseService.get_products(active_only=False)]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
