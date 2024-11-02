import requests
from bs4 import BeautifulSoup

cookies = {
    '__Secure-refresh-token': '6.48252558.A9oSK4RISAqFQvM0M_Mi-A.82.AZsQEv-NrVYMk6yMW65fCWP0XxVDNiCK3xzF9yDvpG2SJjHVR2XZLmgmOSLtK6B8XU3ZPzWqIRsfsjQ7VzJdkYg.20200706222843.20241102110258.5EvKGsGaq7cQuIagWEkaDP6QqeS596D4cF20HiZ6wIs.186f0dbd7df11cf76',
    'abt_data': '7.yFKtehl6ZRUhFUSi8QjeiqVegIcLupgxNAM7uW7DtM-uoc-bJxNf-dLZ-TIDNgWcqABG0-hrT5IGJM2xwyE1mAMmVv0dkrAtM0brDf_MDkKCn8sE8M13tGnJsJGbzfb_WVQXiVHkTa721qwXO1_l26AuFOEMGGtN4-Gyyne9ckS8ZDdwrW_DfY90U7YHcf87jlYdBHXtbgBJiouC7gCuX2pSCm0a4ZX43fnR3vubsQkDX0MazKo7TKLmErc2hsxUnfY1jkucGTb2fceMDK0QZi3hauCyVIFvZixM9GyrwSFF8mspuvaNFvmUfbmCD_9oqVe3GUmhqnVkBHOZpfaHfQFZIL7NtHo3kGjWjl6p8wI33K122Vj7P6ffz1zDKgq0N9MtnwclllMATTgLN7H7sav1dtBW9h3k1LHBMDDSinQxMTmaT6Oy7Gb90xjXsE0RF4wCNhdOeOze_cNHOlDqNh-sr9oHaEwVhGKd-2MNMwDMIFdyf3u6Ax7xszJhLkBw8CKD5Mbt_nldPeF4V_p7xz6b2YEfKLouU9BW',
}

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
}

response = requests.get(
    "https://www.ozon.ru/category/avtomobili-39803/",
    cookies=cookies,
    headers=headers,
)
products = []


if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'lxml')

    price_products = soup.find_all('span', class_='c3019-a1 tsHeadline500Medium c3019-b1 c3019-a6')
    name_products = soup.find_all('div', class_='x2 x7 x9 pj7_23')

    for name_product, price_product in zip(name_products, price_products):
        product_name = name_product.find('span', class_='tsBody500Medium').text.strip()
        product_price = price_product.text.strip()
        product_info = f"Товар: {product_name}, цена: {product_price}"
        products.append(product_info)

    for product in products:
        print(product)
else:
    print(f'Ошибка при выполнении запроса: {response.status_code}')
