from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime, Date,
    ForeignKey, Table, func
)
from sqlalchemy.orm import declarative_base, relationship, backref
from datetime import datetime, timedelta

Base = declarative_base()

class PriceAlert(Base):
    __tablename__ = 'price_alert'  # add if not already there

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    target_price = Column(Float, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    notified = Column(Boolean, default=False)