"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CustomerBase(BaseModel):
    """Base customer model."""
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    budget: Optional[float] = Field(None, ge=0)
    requirements: Optional[str] = None
    buying_timeline: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Create customer request."""
    pass


class CustomerUpdate(BaseModel):
    """Update customer request."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    budget: Optional[float] = None
    requirements: Optional[str] = None
    buying_timeline: Optional[str] = None
    lead_status: Optional[str] = None
    sentiment: Optional[str] = None


class CustomerResponse(CustomerBase):
    """Customer response model."""
    id: int
    lead_status: str
    sentiment: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AppointmentBase(BaseModel):
    """Base appointment model."""
    customer_id: int
    appointment_date: datetime
    reason: Optional[str] = None
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    """Create appointment request."""
    pass


class AppointmentUpdate(BaseModel):
    """Update appointment request."""
    appointment_date: Optional[datetime] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    """Appointment response model."""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    """Base conversation model."""
    customer_id: int
    message_type: str
    content: str


class ConversationCreate(ConversationBase):
    """Create conversation request."""
    pass


class ConversationResponse(ConversationBase):
    """Conversation response model."""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


class CallSummaryBase(BaseModel):
    """Base call summary model."""
    customer_id: int
    summary: str
    requirements: Optional[str] = None
    budget: Optional[float] = None
    sentiment: Optional[str] = None
    lead_classification: Optional[str] = None
    duration_seconds: Optional[int] = None


class CallSummaryCreate(CallSummaryBase):
    """Create call summary request."""
    pass


class CallSummaryResponse(CallSummaryBase):
    """Call summary response model."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Chat request model."""
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    message: str = Field(..., min_length=1)
    conversation_history: Optional[List[tuple]] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    customer_id: Optional[int] = None
    timestamp: datetime
    lead_status: Optional[str] = None


class CallSummaryRequest(BaseModel):
    """Call summary generation request."""
    customer_id: int
    conversation_history: List[tuple]


class VoiceMessageRequest(BaseModel):
    """Voice message processing request."""
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    audio_base64: str
    conversation_history: Optional[List[tuple]] = None


class LeadQualificationRequest(BaseModel):
    """Lead qualification request."""
    customer_id: int
    budget: Optional[float] = None
    buying_timeline: Optional[str] = None
    requirements_text: Optional[str] = None
    sentiment_text: Optional[str] = None


class LeadQualificationResponse(BaseModel):
    """Lead qualification response."""
    customer_id: int
    lead_status: str
    sentiment: str
    requirements_match: float
    reasoning: str


class ProductResponse(BaseModel):
    """Product response model."""
    id: int
    name: str
    model: str
    price: float
    processor: str
    ram: str
    storage: str
    display: str
    gpu: Optional[str]
    battery_life: Optional[str]
    weight: Optional[str]
    description: Optional[str]
    stock: int
    
    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    """Dashboard statistics model."""
    total_customers: int
    hot_leads: int
    warm_leads: int
    cold_leads: int
    scheduled_appointments: int
    completed_appointments: int
    average_sentiment: str
    conversation_count: int
