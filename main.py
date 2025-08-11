import os
import smtplib
import time
from datetime import datetime
from email.message import EmailMessage

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import PriceAlert, Product
from dotenv import load_dotenv
import logging

load_dotenv()  # <-- Make sure this is called before getenv

logging.basicConfig(
    filename='price_alerts.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

SECRET = os.getenv("SECRET")
SECRET_URL = os.getenv("SECRET_URL")
RENDER_DATABASE_URL = os.getenv("RENDER_DATABASE_URL")

engine = create_engine(RENDER_DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def wait_for_url(url, timeout=10, wait_seconds=4*60, max_attempts=30):
    """Poll a URL until status 200 or max attempts reached. Returns True/False."""
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return True
            else:
                logging.info(f"[Wait] Got {response.status_code} from {url}, retrying in {wait_seconds//60} mins...")
        except requests.RequestException as e:
            logging.info(f"[Wait] Request failed for {url}: {e}, retrying in {wait_seconds//60} mins...")

        time.sleep(wait_seconds)

    logging.warning(f"[Wait] Max attempts reached for {url}. Giving up.")
    return False


def send_email(user_email, price_alert):
    try:
        if not price_alert.product:
            logging.warning(f"PriceAlert ID {price_alert.id} has no product associated.")
            return False

        product_name = price_alert.product.name
        target_price = price_alert.target_price
        product_price = price_alert.product.price
        product_image_url = f"https://chocolate-website-95b5.onrender.com/static/{price_alert.product.image or 'default.jpg'}"
        if not wait_for_url(product_image_url):
            logging.warning(f"Image URL not available: {product_image_url}")
            # Optionally continue with sending email without image or return False
            # return False

        # rest of your email sending code...


        subject = f"Price Alert: {product_name} reached your target price"

        text_body = (
            f"Hi,\n\n"
            f"The product {product_name} has reached your target price of £{target_price:.2f}.\n"
            f"Current price: £{product_price:.2f}\n"
            f"Check it out!\n\n"
            "Thanks!"
        )

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Price Alert!</h2>
                <p>The product <strong>{product_name}</strong> has reached your target price of <strong>£{target_price:.2f}</strong>.</p>
                <p>Current price: <strong>£{product_price:.2f}</strong></p>
                <p><img src="{product_image_url}" alt="{product_name}" style="max-width:200px; height:auto;"></p>
                <p>Check it out on our website!</p>
                <p>https://chocolate-website-95b5.onrender.com/product/{price_alert.product_id}</p>
                <br>
                <p>Thanks for shopping with us!</p>
            </body>
        </html>
        """

        CHOC_EMAIL = os.getenv("CHOC_EMAIL")
        CHOC_PASSWORD = os.getenv("CHOC_PASSWORD")

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = CHOC_EMAIL
        msg["To"] = user_email
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype='html')

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(CHOC_EMAIL, CHOC_PASSWORD)
            smtp.send_message(msg)

        logging.info(f"[Email] Sent successfully to {user_email} for product {product_name}")
        return True

    except Exception as e:
        logging.error(f"[Email Error]: {e}")
        return False

def delete_expired_alerts():
    now = datetime.utcnow()
    expired_alerts = session.query(PriceAlert).filter(PriceAlert.expires_at < now).all()
    if not expired_alerts:
        logging.info("No expired price alerts found.")
        return
    count = len(expired_alerts)
    for alert in expired_alerts:
        session.delete(alert)
    session.commit()
    logging.info(f"Deleted {count} expired price alert(s).")

delete_expired_alerts()

alerts_to_notify = (
    session.query(PriceAlert)
    .join(Product, PriceAlert.product_id == Product.id)
    .filter(PriceAlert.target_price >= Product.price)
    .filter(PriceAlert.notified == False)
    .all()
)
if not alerts_to_notify:
    logging.info("No price alerts matches found")
else:
    for alert in alerts_to_notify:
        if alert.user and alert.product:
            success = send_email(alert.user.email, alert)
            if success:
                alert.notified = True
                logging.info(f"Notification sent for alert ID {alert.id}, product {alert.product.name}")
            else:
                logging.error(f"Failed to send notification for alert ID {alert.id}")
        else:
            logging.warning(f"Skipping alert ID {alert.id} due to missing user or product.")
    session.commit()




