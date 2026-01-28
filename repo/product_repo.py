import aiosqlite
from database import DB_PATH, PRODUCTS, PRODUCT_NAME_INDEX
from entityes.product import Product


async def add_product(product: Product) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO products (name, cost, amount) VALUES (?, ?, ?);",
            (product.name, product.cost, product.amount),
        )
        await db.commit()
        product_id = cursor.lastrowid

    product.id = product_id
    PRODUCTS[product_id] = product
    if product.name is not None:
        PRODUCT_NAME_INDEX[product.name] = product_id
    return product_id


async def get_product(product_id: int) -> Product | None:
    cached = PRODUCTS.get(product_id)
    if cached is not None:
        return cached

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, cost, amount FROM products WHERE id = ?;",
            (product_id,),
        )
        row = await cursor.fetchone()

    if not row:
        return None

    product = Product(id=row[0], name=row[1], cost=row[2], amount=row[3])
    PRODUCTS[product.id] = product
    PRODUCT_NAME_INDEX[product.name] = product.id
    return product


async def get_product_by_name(name: str) -> Product | None:
    product_id = PRODUCT_NAME_INDEX.get(name)
    if product_id is not None:
        cached = PRODUCTS.get(product_id)
        if cached is not None:
            return cached

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, cost, amount FROM products WHERE name = ?;",
            (name,),
        )
        row = await cursor.fetchone()

    if not row:
        return None

    product = Product(id=row[0], name=row[1], cost=row[2], amount=row[3])
    PRODUCTS[product.id] = product
    PRODUCT_NAME_INDEX[product.name] = product.id
    return product


async def update_product(product: Product) -> None:
    if product.id is None:
        raise ValueError("update_product: product.id is required")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE products SET name = ?, cost = ?, amount = ? WHERE id = ?;",
            (product.name, product.cost, product.amount, product.id),
        )
        await db.commit()

    PRODUCTS[product.id] = product
    if product.name is not None:
        PRODUCT_NAME_INDEX[product.name] = product.id


async def delete_product(product_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM products WHERE id = ?;", (product_id,))
        await db.commit()

    removed = PRODUCTS.pop(product_id, None)
    if removed is not None and removed.name is not None:
        if PRODUCT_NAME_INDEX.get(removed.name) == product_id:
            PRODUCT_NAME_INDEX.pop(removed.name, None)


async def list_products() -> list[Product]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, name, cost, amount FROM products ORDER BY id;")
        rows = await cursor.fetchall()

    result: list[Product] = []
    for row in rows:
        p = Product(id=row[0], name=row[1], cost=row[2], amount=row[3])
        result.append(p)
        PRODUCTS[p.id] = p
        PRODUCT_NAME_INDEX[p.name] = p.id
    return result
