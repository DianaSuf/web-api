import requests
from bs4 import BeautifulSoup

base_url = "https://www.maxidom.ru/catalog/elki-elovye-vetki-girlyandy/"
products = []

# Выполняем GET-запрос к базовому URL
response = requests.get(base_url)
soup = BeautifulSoup(response.text, 'lxml')

# Извлекаем номер последней страницы из пагинации
pagination = soup.find('div', class_='lvl2__content-nav-numbers-number')
last_page = int(pagination.find_all('a')[-1].text.strip())


# Функция для извлечения информации о товарах с текущей страницы
def extract_data_products(soup):
    price_products = soup.find_all('div', class_='l-product__buy')
    name_products = soup.find_all('div', class_='l-product__name')

    for name_product, price_product in zip(name_products, price_products):
        product_name = name_product.find('span', itemprop="name").text.strip()
        product_price = price_product.find('span', itemprop="price").text.strip()
        products.append(f"Товар: {product_name}, цена: {product_price}")


# Обрабатываем каждую страницу(Тк максимальный amount=90, будем обрабатывать каждую страницу)
for page in range(1, last_page + 1):
    current_page_url = f"{base_url}?amount=30&PAGEN_2={page}"
    response = requests.get(current_page_url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'lxml')
        extract_data_products(soup)  # Извлечение товаров с текущей страницы
    else:
        print(f'Ошибка при выполнении запроса: {response.status_code}')

# Печатаем все найденные товары и их цены
for product in products:
    print(product)
