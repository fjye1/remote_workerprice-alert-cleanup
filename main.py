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
RENDER_DATABASE_URL = os.getenv("RENDER_DATABASE_URL2")

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
        lowest_box = price_alert.product.lowest_price_box()
        if lowest_box:
            product_price = lowest_box.price_inr_unit


        product_image_url = f"https://chocolate-website-95b5.onrender.com/static/{price_alert.product.image or 'default.jpg'}"
        #https://chocolate-website-95b5.onrender.com
        if not wait_for_url(product_image_url):
            logging.warning(f"Image URL not available: {product_image_url}")
            # Optionally continue with sending email without image or return False
            # return False

        # rest of your email sending code...


        subject = f"Price Alert: {product_name} reached your target price"

        text_body = (
            f"Hi,\n\n"
            f"The product {product_name} has reached your target price of ₹{target_price:.2f}.\n"
            f"Current price: ₹{product_price:.2f}\n"
            f"Check it out!\n\n"
            "Thanks!"
        )

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Price Alert!</h2>
                <p>The product <strong>{product_name}</strong> has reached your target price of <strong>₹{target_price:.2f}</strong>.</p>
                <p>Current price: <strong>₹{product_price:.2f}</strong></p>
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

def process_price_alerts(session):
    # 1️⃣ Delete expired alerts
    now = datetime.utcnow()
    expired_alerts = session.query(PriceAlert).filter(PriceAlert.expires_at < now).all()
    if expired_alerts:
        count = len(expired_alerts)
        for alert in expired_alerts:
            session.delete(alert)
        session.commit()
        logging.info(f"Deleted {count} expired price alert(s).")
    else:
        logging.info("No expired price alerts found.")

    # 2️⃣ Fetch active alerts
    alerts = (
        session.query(PriceAlert)
        .join(Product)
        .filter(PriceAlert.notified == False)
        .all()
    )

    alerts_to_notify = []

    # 3️⃣ Check each alert against lowest price box
    for alert in alerts:
        if not alert.product:
            logging.warning(f"Alert ID {alert.id} has no product.")
            continue

        lowest_box = alert.product.lowest_price_box()
        if lowest_box and alert.target_price >= lowest_box.price_inr_unit:
            alerts_to_notify.append((alert, lowest_box))

    if not alerts_to_notify:
        logging.info("No price alerts matched current product prices.")
        return

    # 4️⃣ Send notifications
    for alert, lowest_box in alerts_to_notify:
        if not alert.user:
            logging.warning(f"Skipping alert ID {alert.id} due to missing user.")
            continue

        try:
            success = send_email(alert.user.email, alert)
            if success:
                alert.notified = True
                session.delete(alert)  # delete after notifying
                logging.info(f"Notification sent for alert ID {alert.id}, product {alert.product.name} at price {lowest_box.price_inr_unit}")
            else:
                logging.error(f"Failed to send notification for alert ID {alert.id}")
        except Exception as e:
            logging.exception(f"Error sending notification for alert ID {alert.id}: {e}")

    session.commit()

# Run the function
process_price_alerts(session)




