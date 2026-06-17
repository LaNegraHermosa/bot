"""
Script para poblar la base de datos con productos de ejemplo.
Uso: python seed.py
Requiere un archivo .env con SUPABASE_URL y SUPABASE_SERVICE_KEY configurados.
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Configurá SUPABASE_URL y SUPABASE_SERVICE_KEY en tu .env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

PRODUCTOS = [
    {
        "name": "Pizza Margherita",
        "description": "Pizza clásica con mozzarella, albahaca y salsa de tomate",
        "price": 9.99,
        "stock": 50,
        "category": "pizzas",
        "image_url": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400",
    },
    {
        "name": "Hamburguesa Clásica",
        "description": "Carne 200g, lechuga, tomate, cebolla y salsa especial",
        "price": 8.50,
        "stock": 30,
        "category": "hamburguesas",
        "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400",
    },
    {
        "name": "Ensalada César",
        "description": "Lechuga romana, crutones, parmesano y aderezo César",
        "price": 7.25,
        "stock": 20,
        "category": "ensaladas",
        "image_url": "https://images.unsplash.com/photo-1550304943-4f24f54ddde9?w=400",
    },
    {
        "name": "Sushi Variado (8 piezas)",
        "description": "Selección de nigiri y maki con salmón, atún y palta",
        "price": 12.00,
        "stock": 15,
        "category": "sushi",
        "image_url": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=400",
    },
    {
        "name": "Tacos al Pastor",
        "description": "4 tacos con carne al pastor, piña, cilantro y cebolla",
        "price": 6.50,
        "stock": 25,
        "category": "tacos",
        "image_url": "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?w=400",
    },
    {
        "name": "Pasta Carbonara",
        "description": "Spaghetti con huevo, panceta, parmesano y pimienta negra",
        "price": 10.00,
        "stock": 20,
        "category": "pastas",
        "image_url": "https://images.unsplash.com/photo-1612874742237-6526221588e3?w=400",
    },
    {
        "name": "Wrap de Pollo",
        "description": "Tortilla de harina con pollo grillé, verduras y salsa yogurt",
        "price": 7.75,
        "stock": 18,
        "category": "wraps",
        "image_url": "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=400",
    },
    {
        "name": "Brownie con Helado",
        "description": "Brownie de chocolate caliente con helado de vainilla",
        "price": 5.50,
        "stock": 15,
        "category": "postres",
        "image_url": "https://images.unsplash.com/photo-1564355808539-22e5b1b5c1c8?w=400",
    },
    {
        "name": "Limonada Natural",
        "description": "Limonada fresca con menta y hielo",
        "price": 3.00,
        "stock": 100,
        "category": "bebidas",
        "image_url": "https://images.unsplash.com/photo-1621263764928-df1444c5e859?w=400",
    },
    {
        "name": "Café Latte",
        "description": "Espresso doble con leche vaporizada",
        "price": 3.50,
        "stock": 80,
        "category": "bebidas",
        "image_url": "https://images.unsplash.com/photo-1570968915860-54d5c301fa9f?w=400",
    },
]

def seed():
    print("Insertando productos...")
    for p in PRODUCTOS:
        existing = supabase.table("products").select("id").eq("name", p["name"]).execute()
        if existing.data:
            print(f"  ↻ Ya existe: {p['name']} (id={existing.data[0]['id']})")
        else:
            result = supabase.table("products").insert(p).execute()
            print(f"  ✓ Creado: {p['name']} (id={result.data[0]['id']})")
    print(f"\n✅ Seed completado. {len(PRODUCTOS)} productos procesados.")

if __name__ == "__main__":
    seed()
