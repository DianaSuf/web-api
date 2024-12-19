import asyncio
import json

from fastapi import FastAPI, Depends, HTTPException, WebSocket
from starlette.concurrency import run_in_threadpool
from sqlmodel import Field, SQLModel, create_engine, Session, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from Homework import parse_maxidom_products
from starlette.websockets import WebSocketDisconnect

app = FastAPI()
base_url = "https://www.maxidom.ru/catalog/elki-elovye-vetki-girlyandy/"


# Модель базы данных.
class Product(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: str
    price: int

class ConnectionManager:
    # Список для хранения активных WebSocket-соединений.
    def __init__(self):
        self.connections: list[WebSocket] = []

    # Устанавливаем соединение с клиентом и сохраняем WebSocket в списке активных подключений.
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    # Удаляем соединение из списка.
    async def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)

    # Отправка сообщения всем подключенным клиентам.
    async def broadcast(self, event: str, payload: dict):
        message = {"event": event, "payload": payload}
        for conn in self.connections:
            await conn.send_text(json.dumps(message))

# Создаем экземпляр ConnectionManager, который будет управлять WebSocket-соединениями.
manager = ConnectionManager()


# Получении сессии
def get_async_session():
    sqlite_file_name = "parser.db"
    sqlite_url = f"sqlite+aiosqlite:///{sqlite_file_name}"
    engine = create_async_engine(sqlite_url)
    dbsession = async_sessionmaker(engine)
    return dbsession()

async def get_session():
    async with get_async_session() as session:
        yield session

SessionDep = Depends(get_session)

# Функция для создания базы данных и таблиц.
def create_db_and_tables():
    sqlite_file_name = "parser.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"
    engine = create_engine(sqlite_url)
    SQLModel.metadata.create_all(engine)

# Фоновая задача для периодического парсинга. Будет выполняться раз в 12 часов
async def scheduled_background_parser():
    async with get_async_session() as session:
        while True:
            await asyncio.sleep(12 * 60 * 60)
            await background_parser_async(session)

# Основная асинхронная функция парсинга
async def background_parser_async(session: Session):
    print("Fetching products")
    # Получаем список товаров из парсера
    products_data = await run_in_threadpool(parse_maxidom_products, base_url)

    # Проверяем, есть ли уже такие товары в базе данных
    existing_products = await session.execute(select(Product))
    existing_titles = {product.title for product in existing_products.scalars().all()}

    # Добавляем новые товары в базу данных
    new_products = []
    for product in products_data:
        product_name = product['name']
        product_price = product['price']

        if product_name not in existing_titles:
            new_product = Product(title=product_name, price=int(product_price))
            session.add(new_product)
            new_products.append(new_product)

    await session.commit()
    if new_products:
        await manager.broadcast(event="background_task", payload={"message": "Products loaded"})
    else:
        await manager.broadcast(event="background_task", payload={"message": "No updates"})


@app.on_event("startup")
async def startup_event():
    create_db_and_tables()
    asyncio.create_task(scheduled_background_parser())

@app.get("/start_parser")
async def start_parser(session: Session = SessionDep):
    asyncio.create_task(background_parser_async(session))
    return {"status": "data create"}

@app.get("/products")
async def read_items(session: Session = Depends(get_session), offset: int = 0, limit: int = 100):
    stmt = select(Product).offset(offset).limit(limit)
    items = await session.scalars(stmt)
    return items.all()

@app.get("/products/{item_id}")
async def read_item(item_id: int, session: Session = Depends(get_session)):
    product = await session.get(Product, item_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{item_id}")
async def update_item(item_id: int, data: Product, session: Session = Depends(get_session)):
    # Проверяем, существует ли объект с таким ID
    product_db = await session.get(Product, item_id)
    if not product_db:
        # Отправляем сообщение в вебсокеты об ошибке
        await manager.broadcast(event="error", payload={"message": "Product not found", "item_id": item_id})
        raise HTTPException(status_code=404, detail="Product not found")
    product_data = data.model_dump(exclude_unset=True)
    product_db.sqlmodel_update(product_data)
    session.add(product_db)
    await session.commit()
    await session.refresh(product_db)
    # Отправляем сообщение в вебсокеты о успешном изменении
    await manager.broadcast(event="product_updated", payload=product_db.dict())
    return product_db

@app.post("/products/create")
async def create_item(item: Product, session: Session = Depends(get_session)):
    # Проверяем, существует ли объект с таким ID
    existing_product = await session.get(Product, item.id)
    if existing_product:
        # Отправляем сообщение в вебсокеты об ошибке
        await manager.broadcast(event="error", payload={"message": "Продукт с таким id уже существует", "id": item.id})
        raise HTTPException(status_code=400, detail="Продукт с таким id уже существует")

    # Если объекта с таким ID нет, добавляем его
    session.add(item)
    await session.commit()
    await session.refresh(item)
    # Отправляем сообщение в вебсокеты о создании
    await manager.broadcast(event="product_created", payload=item.dict())
    return item

@app.delete("/products/{item_id}")
async def delete_item(item_id: int, session: Session = Depends(get_session)):
    product = await session.get(Product, item_id)
    if not product:
        # Отправляем сообщение в вебсокеты при ошибке
        await manager.broadcast(event="error", payload={"message": "Product not found", "item_id": item_id})
        raise HTTPException(status_code=404, detail="Product not found")

    await session.delete(product)
    await session.commit()
    # Отправляем сообщение в вебсокеты об успешном удалении
    await manager.broadcast(event="product_deleted",
                            payload={"message": "Product successfully deleted", "item_id": item_id})
    return {"status": "item deleted"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received WebSocket message: {data}")
    except WebSocketDisconnect:
        print(f"Client {websocket} disconnect")
