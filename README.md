# Проект: Сбор данных о книгах с books.toscrape.com

## Описание
Этот проект осуществляет веб-скрейпинг первых 3 страниц каталога книг с сайта [Books to Scrape](http://books.toscrape.com) и сохраняет результаты в двух форматах:
- **books.json** — сгруппировано по рейтингу (1–5)
- **books.xml** — сгруппировано по наличию (in_stock / out_of_stock)

## Структура данных

Каждая книга представлена словарём со следующими полями:
- `title` (string)  
- `price` (string)  
- `availability` (boolean)  
  `True`, ` instock availability">`  `"In stock"`  `False`.
- `rating` (integer)  
  - `"One"` → 1  
  - `"Two"` → 2  
  - `"Three"` → 3  
  - `"Four"` → 4  
  - `"Five"` → 5 

- `product_page_url` (string)  
- `image_url` (string)  
- `category` (string)  
- `upc` (string)  

Импорты 

import requests                       # для отправки HTTP-запросов
from bs4 import BeautifulSoup         # для парсинга HTML
import json                           # для сериализации в JSON
import xml.etree.ElementTree as ET    # для создания XML-структуры
from urllib.parse import urljoin      # для объединения базового и относительного URL