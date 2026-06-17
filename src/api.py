from fastapi import FastAPI, Request, Response, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from twilio.twiml.messaging_response import MessagingResponse
from pydantic import BaseModel
from typing import Optional

from .handlers.whatsapp import whatsapp_handler
from .config import settings

app = FastAPI(title="Bot Multi-plataforma")

# CORS para web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo para mensajes web
class WebMessage(BaseModel):
    message: str
    user_id: str
    platform: str  # "web", "whatsapp", etc.

# Endpoint para WhatsApp/Twilio
@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    phone = form.get("From", "").replace("whatsapp:", "")
    message = form.get("Body", "")
    
    response_text = await whatsapp_handler.handle_message(phone, message)
    
    twiml = MessagingResponse()
    twiml.message(response_text)
    
    return Response(content=str(twiml), media_type="application/xml")

# Endpoint para chat web
@app.post("/web/chat")
async def web_chat(message_data: WebMessage):
    response_text = await whatsapp_handler.handle_message(
        message_data.user_id, 
        message_data.message
    )
    return {"response": response_text}

# Endpoint para obtener productos (API pública)
@app.get("/api/products")
async def get_products(category: Optional[str] = None):
    from .services.database import DatabaseService
    products = DatabaseService.get_products(category=category)
    return [p.model_dump() for p in products]

# ============================================
# Admin Dashboard (HTML)
# ============================================
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel Admin - Bot Tienda</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }}
        .header {{ background: #1a1a2e; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ font-size: 1.5rem; }}
        .container {{ max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .stat-card {{ background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-card h3 {{ font-size: 0.875rem; color: #666; margin-bottom: 0.5rem; }}
        .stat-card .value {{ font-size: 2rem; font-weight: bold; color: #1a1a2e; }}
        .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 1.5rem; overflow: hidden; }}
        .card-header {{ padding: 1rem 1.5rem; border-bottom: 1px solid #eee; font-weight: 600; display: flex; justify-content: space-between; align-items: center; }}
        .card-body {{ padding: 1.5rem; overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ text-align: left; padding: 0.75rem; border-bottom: 1px solid #eee; font-size: 0.875rem; }}
        th {{ color: #666; font-weight: 600; }}
        .badge {{ display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }}
        .badge-pending {{ background: #fff3cd; color: #856404; }}
        .badge-confirmed {{ background: #cce5ff; color: #004085; }}
        .badge-preparing {{ background: #d4edda; color: #155724; }}
        .badge-ready {{ background: #d4edda; color: #155724; }}
        .badge-delivered {{ background: #cce5ff; color: #004085; }}
        .badge-cancelled {{ background: #f8d7da; color: #721c24; }}
        .btn {{ display: inline-block; padding: 0.375rem 0.75rem; border-radius: 4px; border: none; cursor: pointer; font-size: 0.8rem; text-decoration: none; }}
        .btn-primary {{ background: #1a1a2e; color: white; }}
        .btn-danger {{ background: #dc3545; color: white; }}
        .btn-sm {{ padding: 0.25rem 0.5rem; font-size: 0.75rem; }}
        .loading {{ text-align: center; padding: 2rem; color: #666; }}
        .error {{ color: #721c24; background: #f8d7da; padding: 1rem; border-radius: 4px; }}
        .actions {{ display: flex; gap: 0.5rem; }}
        select {{ padding: 0.25rem; border-radius: 4px; border: 1px solid #ccc; }}
        @media (max-width: 768px) {{ .stats {{ grid-template-columns: 1fr 1fr; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Panel de Administración</h1>
        <span id="refresh-time"></span>
    </div>
    <div class="container">
        <div class="stats" id="stats"></div>
        <div class="card">
            <div class="card-header">
                <span>📦 Órdenes Recientes</span>
                <button class="btn btn-primary btn-sm" onclick="loadData()">↻ Actualizar</button>
            </div>
            <div class="card-body" id="orders-table"><div class="loading">Cargando...</div></div>
        </div>
        <div class="card">
            <div class="card-header"><span>🛍 Productos</span></div>
            <div class="card-body" id="products-table"><div class="loading">Cargando...</div></div>
        </div>
    </div>
    <script>
    function statusBadge(status) {
        return `<span class="badge badge-${status}">${status}</span>`;
    }

    async function loadData() {
        try {
            const [statsRes, ordersRes, productsRes] = await Promise.all([
                fetch('/admin/api/stats'),
                fetch('/admin/api/orders'),
                fetch('/admin/api/products')
            ]);
            const stats = await statsRes.json();
            const orders = await ordersRes.json();
            const products = await productsRes.json();

            document.getElementById('refresh-time').textContent = new Date().toLocaleString();

            // Stats
            document.getElementById('stats').innerHTML = `
                <div class="stat-card"><h3>Órdenes Totales</h3><div class="value">${stats.total_orders}</div></div>
                <div class="stat-card"><h3>Pendientes</h3><div class="value">${stats.pending_orders}</div></div>
                <div class="stat-card"><h3>Clientes</h3><div class="value">${stats.total_customers}</div></div>
                <div class="stat-card"><h3>Productos</h3><div class="value">${stats.total_products}</div></div>
                <div class="stat-card"><h3>Ingresos Totales</h3><div class="value">$${stats.total_revenue}</div></div>
            `;

            // Orders
            if (orders.length === 0) {
                document.getElementById('orders-table').innerHTML = '<p>No hay órdenes aún.</p>';
            } else {
                document.getElementById('orders-table').innerHTML = `
                    <table>
                        <thead><tr>
                            <th>ID</th><th>Cliente</th><th>Total</th><th>Estado</th><th>Fecha</th><th>Acción</th>
                        </tr></thead>
                        <tbody>${orders.map(o => `
                            <tr>
                                <td>#${o.id}</td>
                                <td>${o.customer_name || '—'}</td>
                                <td>$${o.total}</td>
                                <td>${statusBadge(o.status)}</td>
                                <td>${new Date(o.created_at).toLocaleDateString()}</td>
                                <td>
                                    <select onchange="updateOrder(${o.id}, this.value)" class="btn-sm">
                                        <option value="">Cambiar estado</option>
                                        <option value="confirmed">Confirmar</option>
                                        <option value="preparing">Preparando</option>
                                        <option value="ready">Listo</option>
                                        <option value="delivered">Entregado</option>
                                        <option value="cancelled">Cancelar</option>
                                    </select>
                                </td>
                            </tr>
                        `).join('')}</tbody>
                    </table>
                `;
            }

            // Products
            if (products.length === 0) {
                document.getElementById('products-table').innerHTML = '<p>No hay productos.</p>';
            } else {
                document.getElementById('products-table').innerHTML = `
                    <table>
                        <thead><tr>
                            <th>ID</th><th>Nombre</th><th>Precio</th><th>Stock</th><th>Categoría</th><th>Activo</th>
                        </tr></thead>
                        <tbody>${products.map(p => `
                            <tr>
                                <td>${p.id}</td>
                                <td>${p.name}</td>
                                <td>$${p.price}</td>
                                <td>${p.stock}</td>
                                <td>${p.category || '—'}</td>
                                <td>${p.active ? '✅' : '❌'}</td>
                            </tr>
                        `).join('')}</tbody>
                    </table>
                `;
            }
        } catch (err) {
            document.getElementById('orders-table').innerHTML = '<div class="error">Error al cargar datos. ¿El servidor está corriendo?</div>';
            document.getElementById('products-table').innerHTML = '';
        }
    }

    async function updateOrder(orderId, status) {
        if (!status) return;
        try {
            const res = await fetch('/admin/api/orders/' + orderId + '/status', {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({status})
            });
            if (res.ok) loadData();
            else alert('Error al actualizar');
        } catch (err) {
            alert('Error de conexión');
        }
    }

    loadData();
    setInterval(loadData, 30000);
    </script>
</body>
</html>
"""

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    return ADMIN_HTML

# Admin API endpoints
@app.get("/admin/api/stats")
async def admin_stats():
    from .services.database import DatabaseService
    return DatabaseService.get_admin_stats()

@app.get("/admin/api/orders")
async def admin_orders():
    from .services.database import DatabaseService
    return DatabaseService.get_all_orders()

@app.get("/admin/api/products")
async def admin_products():
    from .services.database import DatabaseService
    return [p.model_dump() for p in DatabaseService.get_products(active_only=False)]

@app.patch("/admin/api/orders/{order_id}/status")
async def admin_update_order_status(order_id: int, data: dict):
    from .services.database import DatabaseService
    status = data.get("status")
    if status not in ("pending", "confirmed", "preparing", "ready", "delivered", "cancelled"):
        raise HTTPException(status_code=400, detail="Estado inválido")
    success = DatabaseService.update_order_status(order_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)