import requests
import re
from bs4 import BeautifulSoup

url = "https://www.ryanscomputers.com/category/laptop-all-laptop?limit=100&page=1"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")
total_items_html_snippet = str(soup.find("span", class_="found-text"))
match = re.search(r'\((\d+)\s*Products found\)', total_items_html_snippet)
total_laptop_count = int(match.group(1))
page_count = int(total_laptop_count/100)
total_available_laptop_count = 0
for i in range(1, page_count+1):
    i = str(i)
    url = "https://www.ryanscomputers.com/category/laptop-all-laptop?limit=100&sort=LH&page=" + i
    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")
    product_names = soup.find_all('p', class_='card-text p-0 m-0 list-view-text')
    product_prices = soup.find_all('p', class_='pr-text cat-sp-text pb-1')

    for product_name, product_price in zip(product_names, product_prices):
        product_name = product_name.find('a').text.strip()
        comma_count = product_price.text.count(',')
        if comma_count == 2:
            match = re.search(r'\b(\d{1,3}(?:,\d{3})*\b)', product_price.text)
            if match:
                extracted_value = match.group(1)
                if extracted_value != '0':
                    print(product_name)
                    print(extracted_value)
                    total_available_laptop_count = total_available_laptop_count + 1
        else:
            text = str(product_price.text)
            match = re.search(r'(\d{1,3}(?:,\d{3})*)', text)
            if match:
                extracted_value = match.group(1)
                if extracted_value != '0':
                    print(product_name)
                    print(extracted_value)
                    total_available_laptop_count = total_available_laptop_count + 1

print('Total Laptop Counts in Ryans Computers: ', total_laptop_count)
print('Total Available Laptop Counts: ', total_available_laptop_count)
