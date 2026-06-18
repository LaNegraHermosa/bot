# Bot Multi-plataforma para Negocio

Bot automatizado para gestión de pedidos y ventas en Telegram, WhatsApp (Twilio opcional) y Web.

## Características

- **Multi-plataforma**: Telegram, WhatsApp (Twilio opcional) y Web
- **Gestión de productos**: Catálogo con imágenes, precios y stock
- **Carrito persistente en DB**: Tabla `carts` en PostgreSQL, no en memoria
- **Stock atómico**: `SELECT FOR UPDATE` vía RPC `atomic_decrement_stop`
- **Dashboard admin**: Panel web en `/admin` con stats, órdenes y productos
- **Admin auth**: HTTP Basic con bcrypt
- **API REST**: Endpoints públicos y admin

## Estructura

```
src/
├── api.py           # FastAPI: webhook WhatsApp, chat web, /admin, /api
├── config.py        # Variables de entorno (Settings)
├── database.py      # Conexión lazy a Supabase
├── main.py          # Entrypoint: Telegram bot + FastAPI concurrente
├── handlers/
│   ├── telegram.py  # Handlers Telegram
│   └── whatsapp.py  # Handlers WhatsApp
├── models/
│   └── __init__.py  # Pydantic: Product, Customer, Order, OrderItem, CartItem
└── services/
    ├── database.py  # CRUD a Supabase (productos, clientes, carrito, órdenes)
    └── cart.py      # Lógica de carrito (delega a DatabaseService)
```

## Instalación

```bash
pip install -r requirements.txt
```

## Variables de entorno (`.env`)

```
TELEGRAM_BOT_TOKEN=tu_token

SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_KEY=tu_service_key

ADMIN_USER=admin
ADMIN_PASSWORD=clave-segura

HOST=0.0.0.0
PORT=8000
ENV=development

CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Opcionales (solo si usas Twilio)
# TWILIO_ACCOUNT_SID=
# TWILIO_AUTH_TOKEN=
# TWILIO_WHATSAPP_NUMBER=
```

## Configuración de Supabase

Ejecutar `supabase_migration.sql` en tu proyecto Supabase (SQL Editor). Crea:

- `products`, `customers`, `orders`, `order_items`, `carts`
- Índices y triggers `updated_at`
- Función RPC `atomic_decrement_stock` con `FOR UPDATE`

Poblar datos de ejemplo:
```bash
python seed.py
```

## Uso

```bash
python src/main.py
```

Inicia el bot de Telegram y la API concurrentemente.

### Endpoints

| Ruta | Auth | Descripción |
|------|------|-------------|
| `GET /api/products` | No | Catálogo público |
| `POST /web/chat` | No | Chat web (usa WhatsAppHandler) |
| `POST /whatsapp/webhook` | No | Webhook Twilio (solo si configurado) |
| `GET /admin` | Basic | Dashboard admin |
| `GET /admin/api/stats` | Basic | Stats (órdenes, clientes, ingresos) |
| `GET /admin/api/orders` | Basic | Lista de órdenes |
| `GET /admin/api/products` | Basic | Lista de productos (incluye inactivos) |

## Comandos WhatsApp

- `hola` / `inicio` — Bienvenida
- `productos` — Catálogo
- `carrito` — Ver carrito
- `agregar [id]` — Agregar producto (ej: `agregar 1`)
- `confirmar` — Finalizar pedido

## Licencia

MIT
