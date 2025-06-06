import requests                    
from bs4 import BeautifulSoup       
import json                         
import xml.etree.ElementTree as ET    
from urllib.parse import urljoin      

BASE_URL = "http://books.toscrape.com/"
CATALOG_URL = urljoin(BASE_URL, "catalogue/page-{}.html") 

def parse_book_detail(url):
    # Делает запрос к detail-странице книги и возвращает (category, upc)
    r = requests.get(url)
    r.raise_for_status()  #200!=
    soup = BeautifulSoup(r.text, "html.parser")

    crumbs = [li.get_text(strip=True) for li in soup.select("ul.breadcrumb li")]
    category = crumbs[2] if len(crumbs) >= 3 else "" #3li

    # UPC
    upc = ""
    for row in soup.select("table.table-striped tr"):
        header = row.find("th").get_text(strip=True)
        if header == "UPC":
            upc = row.find("td").get_text(strip=True)
            break

    return category, upc

def parse_page(page_number):
    url = CATALOG_URL.format(page_number)
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    books = []

    for art in soup.select("article.product_pod"):
        a = art.find("h3").find("a")
        detail_url = urljoin(url, a["href"]) 
        title = a["title"].strip()

        price = art.select_one("p.price_color").get_text(strip=True)

        avail_txt = art.select_one("p.instock.availability").get_text(strip=True)
        availability = "In stock" in avail_txt

        cls_list = art.find("p", class_="star-rating")["class"]
        star = [c for c in cls_list if c != "star-rating"][0]
        rating = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}.get(star, 0)

        image_url = urljoin(url, art.find("img")["src"])
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
    result = []
    for i in range(1, n_pages + 1):
        result += parse_page(i)
    return result

def save_json(books, fname="books.json"):
    grouped = {str(i): [] for i in range(1, 6)} 

    for b in books:
        r = str(b["rating"])
        grouped.setdefault(r, []).append(b)

    with open(fname, "w", encoding="utf-8") as f:
        json.dump(grouped, f, ensure_ascii=False, indent=2)

def save_xml(books, fname="books.xml"):
    root = ET.Element("catalogue")        
    in_s = ET.SubElement(root, "in_stock")  
    out_s = ET.SubElement(root, "out_of_stock")  

    for b in books:
        # Выбираем раздел в зависимости от доступности книги
        parent = in_s if b["availability"] else out_s
        book_el = ET.SubElement(parent, "book")

        for key in ["title", "price", "availability", "rating", 
                    "product_page_url", "image_url", "category", "upc"]:
            ch = ET.SubElement(book_el, key)
            ch.text = str(b[key])

    # Сериализуем v XML-строку
    raw = ET.tostring(root, encoding="utf-8")

    import xml.dom.minidom as md
    pretty = md.parseString(raw).toprettyxml(indent="  ")

    with open(fname, "w", encoding="utf-8") as f:
        f.write(pretty)

def main():
    books = collect_books(3) # CHANGE n-pages
    save_json(books)       
    save_xml(books)           

main()