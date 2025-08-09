import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import PriceAlert
from dotenv import load_dotenv
import psycopg2


load_dotenv()

RENDER_DATABASE_URL = os.getenv("RENDER_DATABASE_URL")

engine = create_engine(RENDER_DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def delete_expired_alerts():
    now = datetime.utcnow()
    expired_alerts = session.query(PriceAlert).filter(PriceAlert.expires_at < now).all()
    if not expired_alerts:
        print("No expired price alerts found.")
        return
    for alert in expired_alerts:
        session.delete(alert)
    session.commit()
    print(f"Deleted {len(expired_alerts)} expired price alert(s).")

delete_expired_alerts()