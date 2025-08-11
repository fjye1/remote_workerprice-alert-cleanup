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
    product = relationship('Product')
    user = relationship('User', back_populates='price_alerts')


class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    image = Column(String(200))


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False)

    price_alerts = relationship('PriceAlert', back_populates='user')