"""Database models for the Sales Voice Agent."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Customer(Base):
    """Customer lead model."""
    
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    budget = Column(Float, nullable=True)
    requirements = Column(Text, nullable=True)
    buying_timeline = Column(String(50), nullable=True)
    lead_status = Column(String(50), default="New")  # New, Hot, Warm, Cold, Qualified
    sentiment = Column(String(50), nullable=True)  # Positive, Neutral, Negative
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name={self.name}, lead_status={self.lead_status})>"


class Appointment(Base):
    """Appointment booking model."""
    
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    reason = Column(String(255), nullable=True)
    status = Column(String(50), default="Scheduled")  # Scheduled, Completed, Cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, customer_id={self.customer_id}, status={self.status})>"


class Conversation(Base):
    """Conversation history model."""
    
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    message_type = Column(String(50))  # user, assistant
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, customer_id={self.customer_id}, type={self.message_type})>"


class CallSummary(Base):
    """Call summary model."""
    
    __tablename__ = "call_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    summary = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    budget = Column(Float, nullable=True)
    sentiment = Column(String(50), nullable=True)
    lead_classification = Column(String(50), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CallSummary(id={self.id}, customer_id={self.customer_id})>"


class Product(Base):
    """Product model for RAG."""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    model = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    processor = Column(String(255), nullable=False)
    ram = Column(String(50), nullable=False)
    storage = Column(String(50), nullable=False)
    display = Column(String(100), nullable=False)
    gpu = Column(String(255), nullable=True)
    battery_life = Column(String(100), nullable=True)
    weight = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    stock = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"
