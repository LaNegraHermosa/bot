# Bot Multi-plataforma para Negocio

🤖 Bot automatizado para gestión de pedidos y ventas en múltiples plataformas.

## Características

- **Multi-plataforma**: Telegram, WhatsApp (Twilio) y Web
- **Gestión de productos**: Catálogo con imágenes, precios y stock
- **Carrito de compras**: Agregar, ver y confirmar pedidos
- **Base de datos Supabase**: Integración completa con PostgreSQL
- **API REST**: Endpoints para chat web y gestión de productos

## Estructura del Proyecto

```
src/
├── api.py           # FastAPI para WhatsApp webhook y chat web
├── config.py        # Configuración y variables de entorno
├── database.py      # Conexión a Supabase
├── main.py          # Punto de entrada para Telegram bot
├── handlers/
│   ├── telegram.py  # Handlers para Telegram
│   └── whatsapp.py  # Handlers para WhatsApp
├── models/
│   └── __init__.py  # Modelos Pydantic (Product, Customer, Order)
└── services/
    ├── database.py  # Operaciones de base de datos
    └── cart.py      # Lógica del carrito de compras
```

## Instalación

1. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

2. **Configurar variables de entorno** (`.env`):
```bash
# Telegram
TELEGRAM_BOT_TOKEN=tu_token_de_botfather

# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=tu_anon_key
SUPABASE_SERVICE_KEY=tu_service_key

# Twilio (WhatsApp)
TWILIO_ACCOUNT_SID=tu_account_sid
TWILIO_AUTH_TOKEN=tu_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

## Configuración de Supabase

Crear las siguientes tablas en tu proyecto Supabase:

### products
| column | type |
|--------|------|
| id | bigint (auto) |
| name | text |
| description | text |
| price | numeric |
| stock | int |
| category | text |
| image_url | text |
| active | boolean |

### customers
| column | type |
|--------|------|
| id | bigint (auto) |
| telegram_id | bigint |
| phone | text |
| name | text |
| email | text |

### orders
| column | type |
|--------|------|
| id | bigint (auto) |
| customer_id | bigint |
| total | numeric |
| status | text |
| notes | text |

### order_items
| column | type |
|--------|------|
| id | bigint (auto) |
| order_id | bigint |
| product_id | bigint |
| quantity | int |
| price | numeric |

## Uso

### Ejecutar Bot de Telegram:
```bash
python src/main.py
```

### Ejecutar API (WhatsApp + Web):
```bash
uvicorn src.api:app --reload
```

### Endpoints disponibles:
- `POST /whatsapp/webhook` - Webhook para Twilio WhatsApp
- `POST /web/chat` - API para chat web
- `GET /api/products` - Lista de productos (pública)

## Funcionalidades

### Para Clientes:
- Ver catálogo de productos
- Agregar productos al carrito
- Ver total del carrito
- Confirmar pedido
- Historial de pedidos

### Comandos de WhatsApp:
- `hola` o `inicio` - Mensaje de bienvenida
- `productos` - Ver catálogo
- `carrito` - Ver carrito
- `agregar [id]` - Agregar producto (ej: `agregar 1`)
- `confirmar` - Finalizar pedido

## Próximos pasos

- [ ] Añadir imágenes de productos en Telegram
- [ ] Implementar notificaciones de estado de pedidos
- [ ] Integrar pasarela de pagos
- [ ] Dashboard administrativo para ver pedidos
- [ ] Gestión de categorías de productos

## Licencia

MIT