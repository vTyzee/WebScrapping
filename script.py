#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
script.py — упрощённый парсер первых 3 страниц с books.toscrape.com.
Сохраняет:
  • books.json — сгруппировано по rating (1–5)
  • books.xml  — сгруппировано по availability (in_stock/out_of_stock)

Комментарии поясняют выбор структуры и отличие JSON и XML.
"""

import requests
from bs4 import BeautifulSoup
import json
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import re

BASE_URL = "http://books.toscrape.com/"
CATALOG_URL = urljoin(BASE_URL, "catalogue/page-{}.html")


def parse_book_detail(url):
    """
    Заходит на страницу книги (detail_url), чтобы получить:
      - category (string): берётся из хлебных крошек <ul class="breadcrumb">
      - upc      (string): берётся из таблицы <table class="table table-striped">
    Возвращает кортеж (category, upc).
    """
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Извлечение категории: ['Home', 'Books', 'Category', 'Title']
    crumbs = [li.get_text(strip=True) for li in soup.select("ul.breadcrumb li")]
    category = crumbs[2] if len(crumbs) >= 3 else ""

    upc = ""
    for row in soup.select("table.table-striped tr"):
        if row.find("th").get_text(strip=True) == "UPC":
            upc = row.find("td").get_text(strip=True)
            break

    return category, upc


def parse_page(page_number):
    """
    Парсит одну страницу каталога (page_number) и возвращает список словарей:
      {
        "title": str,
        "price": str,            # '£xx.xx'
        "availability": bool,    # True, если 'In stock', иначе False
        "rating": int,           # 1–5 (из CSS-класса 'star-rating')
        "product_page_url": str,
        "image_url": str,
        "category": str,
        "upc": str
      }
"""
    url = CATALOG_URL.format(page_number)
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    books = []

    for art in soup.select("article.product_pod"):
        a = art.find("h3").find("a")
        detail_url = urljoin(url, a["href"])
        title = a["title"].strip()

        # Цена вида '£xx.xx'
        price = art.select_one("p.price_color").get_text(strip=True)

        # Наличие: True, если текст содержит 'In stock'
        avail_txt = art.select_one("p.instock.availability").get_text(strip=True)
        availability = "In stock" in avail_txt

        # Рейтинг: CSS-класс вида ['star-rating', 'Three'] → 'Three' → 3
        cls_list = art.find("p", class_="star-rating")["class"]
        star = [c for c in cls_list if c != "star-rating"][0]
        rating = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}.get(star, 0)

        # Абсолютная ссылка на обложку
        image_url = urljoin(url, art.find("img")["src"])

        # Получаем category и upc с detail-страницы
        category, upc = parse_book_detail(detail_url)

        books.append({
            "title": title,
            "price": price,
            "availability": availability,
            "rating": rating,
            "product_page_url": detail_url,
            "image_url": image_url,
            "category": category,
            "upc": upc
        })

    return books


def collect_books(n_pages=3):
    """
    Собирает книги со страниц 1..n_pages включительно.
    Возвращает единый список словарей-книг.
"""
    result = []
    for i in range(1, n_pages + 1):
        print(f"Парсинг страницы {i}...")
        result += parse_page(i)
    return result


def save_json(books, fname="books.json"):
    """
    Сохраняет книги в JSON, сгруппированные по 'rating':
    {
      "1": [ {...}, {...}, ... ],  # книги с рейтингом 1
      ...
      "5": [ {...} ]              # книги с рейтингом 5
    }

JSON-словарь с ключами '1'..'5' служит «быстрым индексом» по рейтингу.
"""
    grouped = {str(i): [] for i in range(1, 6)}
    for b in books:
        r = str(b["rating"])
        grouped.setdefault(r, []).append(b)

    with open(fname, "w", encoding="utf-8") as f:
        json.dump(grouped, f, ensure_ascii=False, indent=2)


def save_xml(books, fname="books.xml"):
    """
    Сохраняет книги в XML, сгруппированные по 'availability':
    <catalogue>
      <in_stock>      <- все книги, у которых availability=True
        <book>
          <title>…</title>
          <price>…</price>
          <availability>True</availability>
          <rating>…</rating>
          <product_page_url>…</product_page_url>
          <image_url>…</image_url>
          <category>…</category>
          <upc>…</upc>
        </book>
        ...
      </in_stock>
      <out_of_stock>  <- все, где availability=False
        <book>…</book>
        ...
      </out_of_stock>
    </catalogue>

Теперь внутри каждого <book> есть тег <availability> с True/False.
"""
    root = ET.Element("catalogue")
    in_s = ET.SubElement(root, "in_stock")
    out_s = ET.SubElement(root, "out_of_stock")

    for b in books:
        parent = in_s if b["availability"] else out_s
        book_el = ET.SubElement(parent, "book")
        for key in ["title", "price", "availability", "rating", "product_page_url", "image_url", "category", "upc"]:
            ch = ET.SubElement(book_el, key)
            ch.text = str(b[key])

    raw = ET.tostring(root, encoding="utf-8")
    import xml.dom.minidom as md
    pretty = md.parseString(raw).toprettyxml(indent="  ")

    with open(fname, "w", encoding="utf-8") as f:
        f.write(pretty)


def main():
    books = collect_books(3)
    save_json(books)
    save_xml(books)


if __name__ == "__main__":
    main()
