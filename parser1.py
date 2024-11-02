import requests
from bs4 import BeautifulSoup

response = requests.get(url="http://e1.ru")
soup = BeautifulSoup(response.content, "lxml")
traffic = soup.find("span", class_="level_3XueO yellow_3XueO text-style-ui-menu-bold")
int_traffic = int(traffic.get_text())
print(int_traffic, type(int_traffic))