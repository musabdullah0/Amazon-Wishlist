import requests
import re
from bs4 import BeautifulSoup
from amazon_wishlist.models import Item
from flask_mail import Message
from amazon_wishlist import mail, db
from datetime import datetime


class Scraper:
    @staticmethod
    def update_db():
        for item in Item.query.all():
            _, price = Scraper.amazon_parser(item.asin)
            item.price = price
            db.session.commit()
            if item.price <= item.alert_price:
                msg = Message(subject="Amazon Wishlist Notification")
                msg.recipients = [item.author.email]
                msg.body = f'Item: {item.title} has fallen below your alert price: {item.alert_price}'
                mail.send(msg)
        print(f'updated at {datetime.now()}')

    @staticmethod
    def amazon_parser(product_id):
        result = [None, None]
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Safari/605.1.15'}
        url = 'https://www.amazon.com/dp/' + product_id
        try:
            page = requests.get(url, headers=headers)
            soup = BeautifulSoup(page.content, "lxml")

            title = soup.find("span", {"id": "productTitle"}).get_text().strip()
            raw_price = soup.find("span", {"id": "priceblock_ourprice"}).get_text().strip()
            s = re.compile('\.')  # regex to find decimal point in price
            # price starts after dollar sign and goes two spots after decimal point
            price = float(raw_price[1: s.search(raw_price).start() + 3].replace(',', ''))
            # data.append({"id": product_id, "title": title, "price": price, "alert_price": alert_price})
            result[0], result[1] = title, price
            return result
        except AttributeError:
            return result
