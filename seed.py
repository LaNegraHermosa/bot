"""
Poblar productos de ejemplo.
Uso: python seed.py
Requiere .env con SUPABASE_URL y SUPABASE_SERVICE_KEY.
"""
import os, sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_SERVICE_KEY")
if not URL or not KEY:
    print("ERROR: Configurá SUPABASE_URL y SUPABASE_SERVICE_KEY en .env")
    sys.exit(1)

supa = create_client(URL, KEY)

PRODUCTOS = [
    {"name":"Pizza Margherita","description":"Mozzarella, albahaca, salsa de tomate","price":9.99,"stock":50,"category":"pizzas","image_url":"https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400"},
    {"name":"Hamburguesa Clásica","description":"Carne 200g, lechuga, tomate, cebolla","price":8.50,"stock":30,"category":"hamburguesas","image_url":"https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400"},
    {"name":"Ensalada César","description":"Lechuga romana, crutones, parmesano","price":7.25,"stock":20,"category":"ensaladas","image_url":"https://images.unsplash.com/photo-1550304943-4f24f54ddde9?w=400"},
    {"name":"Sushi Variado 8pz","description":"Nigiri y maki con salmón, atún y palta","price":12.00,"stock":15,"category":"sushi","image_url":"https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=400"},
    {"name":"Tacos al Pastor","description":"4 tacos con carne al pastor, piña, cilantro","price":6.50,"stock":25,"category":"tacos","image_url":"https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?w=400"},
    {"name":"Pasta Carbonara","description":"Spaghetti con huevo, panceta, parmesano","price":10.00,"stock":20,"category":"pastas","image_url":"https://images.unsplash.com/photo-1612874742237-6526221588e3?w=400"},
    {"name":"Wrap de Pollo","description":"Tortilla con pollo grillé, verduras","price":7.75,"stock":18,"category":"wraps","image_url":"https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=400"},
    {"name":"Brownie con Helado","description":"Brownie de chocolate con helado de vainilla","price":5.50,"stock":15,"category":"postres","image_url":"https://images.unsplash.com/photo-1564355808539-22e5b1b5c1c8?w=400"},
    {"name":"Limonada Natural","description":"Limonada fresca con menta","price":3.00,"stock":100,"category":"bebidas","image_url":"https://images.unsplash.com/photo-1621263764928-df1444c5e859?w=400"},
    {"name":"Café Latte","description":"Espresso doble con leche vaporizada","price":3.50,"stock":80,"category":"bebidas","image_url":"https://images.unsplash.com/photo-1570968915860-54d5c301fa9f?w=400"},
]

def seed():
    print("Insertando productos...")
    for p in PRODUCTOS:
        exist = supa.table("products").select("id").eq("name", p["name"]).execute()
        if exist.data:
            print(f"  ↻ Ya existe: {p['name']} (id={exist.data[0]['id']})")
        else:
            r = supa.table("products").insert(p).execute()
            print(f"  ✓ Creado: {p['name']} (id={r.data[0]['id']})")
    print(f"\n✅ {len(PRODUCTOS)} productos procesados.")

if __name__ == "__main__":
    seed()
