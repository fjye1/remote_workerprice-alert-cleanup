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
    __tablename__ = "product"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    image = Column(String(200))

    # Only keep relationship needed for lowest_price_box()
    boxes = relationship('Box', back_populates='product')

    def lowest_price_box(self):
        arrived_and_active = [
            b for b in self.boxes
            if b.shipment.has_arrived and b.is_active
        ]

        if not arrived_and_active:
            return None

        return min(arrived_and_active, key=lambda b: b.price_inr_unit)


class Box(Base):
    __tablename__ = "box"

    id = Column(Integer, primary_key=True)

    product_id = Column(Integer, ForeignKey('product.id'))
    product = relationship('Product', back_populates='boxes')

    shipment_id = Column(Integer, ForeignKey('shipment.id'))
    shipment = relationship('Shipment', back_populates='boxes')

    # Fields lowest_price_box relies on:
    price_inr_unit = Column(Float)
    is_active = Column(Boolean, default=True)


class Shipment(Base):
    __tablename__ = "shipment"

    id = Column(Integer, primary_key=True)

    has_arrived = Column(Boolean, default=False)

    boxes = relationship('Box', back_populates='shipment')


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False)

    price_alerts = relationship('PriceAlert', back_populates='user')
