"""
SQLAlchemy models for the backtesting database.
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Stock(Base):
    """Stock information table."""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    company_name = Column(String(200))
    sector = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    daily_prices = relationship("DailyPrice", back_populates="stock", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', company_name='{self.company_name}')>"

class DailyPrice(Base):
    """Daily OHLCV price data table."""
    __tablename__ = 'daily_prices'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Numeric(10, 2))
    high = Column(Numeric(10, 2))
    low = Column(Numeric(10, 2))
    close = Column(Numeric(10, 2))
    volume = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    stock = relationship("Stock", back_populates="daily_prices")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('stock_id', 'date', name='uq_stock_date'),
    )
    
    def __repr__(self):
        return f"<DailyPrice(stock_id={self.stock_id}, date='{self.date}', close={self.close})>"
