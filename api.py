import asyncio
from fastapi import FastAPI, Depends, HTTPException
from starlette.concurrency import run_in_threadpool
from sqlmodel import Field, SQLModel, create_engine, Session, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from Homework import parse_maxidom_products

app = FastAPI()
base_url = "https://www.maxidom.ru/catalog/elki-elovye-vetki-girlyandy/"

class Product(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: str
    price: int

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

def create_db_and_tables():
    sqlite_file_name = "parser.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"
    engine = create_engine(sqlite_url)
    SQLModel.metadata.create_all(engine)

async def scheduled_background_parser(session: Session):
    while True:
        await asyncio.sleep(12 * 60 * 60)
        await background_parser_async(session)


async def background_parser_async(session: Session):
    # Получаем список товаров из парсера
    products_data = await run_in_threadpool(parse_maxidom_products, base_url)

    # Проверяем, есть ли уже такие товары в базе данных, чтобы избежать дубликатов
    existing_products = await session.execute(select(Product))
    existing_titles = {product.title for product in existing_products.scalars().all()}

    # Добавляем новые товары в базу данных
    for product in products_data:
        product_name = product['name']
        product_price = product['price']

        # Проверяем, есть ли товар в БД
        if product_name not in existing_titles:
            new_product = Product(title=product_name, price=int(product_price))
            session.add(new_product)

    await session.commit()

@app.on_event("startup")
async def startup_event(session: Session = SessionDep):
    create_db_and_tables()
    asyncio.create_task(scheduled_background_parser(session))

@app.get("/start_parser")
async def start_parser(session: Session = SessionDep):
    asyncio.create_task(background_parser_async(session))
    return {"status": "data create"}

@app.get("/products")
async def read_items(session: Session = SessionDep, offset: int = 0, limit: int = 100):
    stmt = select(Product).offset(offset).limit(limit)
    items = await session.scalars(stmt)
    return items.all()


@app.get("/products/{item_id}")
async def read_item(item_id: int, session: Session = SessionDep):
    product = await session.get(Product, item_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{item_id}")
async def update_item(item_id: int, data: Product, session: Session = SessionDep):
    product_db = await session.get(Product, item_id)
    if not product_db:
        raise HTTPException(status_code=404, detail="Product not found")
    product_data = data.model_dump(exclude_unset=True)
    product_db.sqlmodel_update(product_data)
    session.add(product_db)
    await session.commit()
    await session.refresh(product_db)
    return product_db

@app.post("/products/create")
async def create_item(item: Product, session: Session = SessionDep):
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item

@app.delete("/products/{item_id}")
async def delete_item(item_id: int, session: Session = SessionDep):
    product = await session.get(Product, item_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await session.delete(product)
    await session.commit()
    return {"status": "item delete"}
