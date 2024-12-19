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
    if pagination:
        last_page = int(pagination.find_all('a')[-1].text.strip())
    else:
        print("Ошибка при извлечении последней страницы из пагинации")
        return products

    # Функция для извлечения информации о товарах с текущей страницы
    def extract_data_products(soup):
        price_products = soup.find_all('div', class_='l-product__buy')
        name_products = soup.find_all('div', class_='l-product__name')

        for name_product, price_product in zip(name_products, price_products):
            product_name = name_product.find('span', itemprop="name")
            product_price = price_product.find('span', itemprop="price")

            if product_name and product_price:
                product_name_text = product_name.text.strip()
                product_price_text = product_price.text.strip()
                products.append({'name': product_name_text, 'price': product_price_text})
            else:
                print("Не удалось извлечь данные о товаре")

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
