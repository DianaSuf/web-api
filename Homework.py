import requests
from bs4 import BeautifulSoup


def parse_maxidom_products(base_url):
    products = []

    # Выполняем GET-запрос к базовому URL
    response = requests.get(base_url)
    if response.status_code != 200:
        print(f'Ошибка при выполнении запроса: {response.status_code}')
        return products

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
            products.append({'name': product_name, 'price': product_price})

    # Обрабатываем каждую страницу
    for page in range(1, last_page + 1):
        current_page_url = f"{base_url}?amount=30&PAGEN_2={page}"
        response = requests.get(current_page_url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            extract_data_products(soup)  # Извлечение товаров с текущей страницы
        else:
            print(f'Ошибка при выполнении запроса на странице {page}: {response.status_code}')

    return products


# Проверка: вызов функции из того же файла
if __name__ == "__main__":
    base_url = "https://www.maxidom.ru/catalog/elki-elovye-vetki-girlyandy/"
    result = parse_maxidom_products(base_url)

    # Форматированный вывод
    for product in result:
        print(f"Товар: {product['name']}, цена: {product['price']}")

#
# import requests as rq
# from bs4 import BeautifulSoup
#
#
# def parse_maxidom():
#     products = []
#     url = 'https://www.maxidom.ru/catalog/kraski-i-emali/'
#     while url:
#         response = rq.get(url)
#         soup = BeautifulSoup(response.text, 'lxml')
#
#         # Находим все товары на странице
#         items_name = soup.find_all('div', class_='l-product__name')
#         items_price = soup.find_all('div', class_='l-product__buy')
#
#         for i in range(len(items_name)):
#             title = items_name[i].find('span', itemprop='name').text.strip()
#             price = items_price[i].find('div', class_='l-product__price-base').text.strip()
#             products.append({'title': title, 'price': int("".join(filter(str.isdigit, price)))})
#
#         # Переход на следующую страницу
#         next_page = soup.find('div', class_='lvl2__content-nav-numbers-number').find_all('a')
#         if len(next_page) == 3 and next_page[1]['href'] != '#':
#             url = 'https://www.maxidom.ru' + next_page[1]['href']
#         elif len(next_page) == 4:
#             url = 'https://www.maxidom.ru' + next_page[2]['href']
#         elif len(next_page) == 3 and next_page[1]['href'] == '#':
#             url = 'https://www.maxidom.ru' + next_page[2]['href']
#         else:
#             url = None
#     return products
#
#
# if __name__ == "__main__":
#     product_data = parse_maxidom()
#     for product in product_data:
#         print(f"Товар: {product['title']}, Цена: {product['price']}")