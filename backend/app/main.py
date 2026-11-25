"""FastAPI backend for the AI Sales Voice Agent."""

import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Load environment variables
load_dotenv()

from app.database import init_db, get_db, SessionLocal
from app.database.models import Customer, Conversation, CallSummary, Appointment
from app.models import (
    CustomerResponse, CustomerCreate, CustomerUpdate,
    AppointmentResponse, AppointmentCreate, AppointmentUpdate,
    ConversationResponse, ConversationCreate,
    CallSummaryResponse, CallSummaryCreate,
    ChatRequest, ChatResponse,
    CallSummaryRequest,
    VoiceMessageRequest,
    LeadQualificationRequest, LeadQualificationResponse,
    DashboardStats,
)
from app.agents import SalesAgent
from app.rag import initialize_knowledge_base
from app.lead_qualification import LeadClassifier
from app.appointments import AppointmentManager
from app.voice import SpeechProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Sales Voice Agent",
    description="Autonomous AI-powered sales agent with voice interaction",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
sales_agent = None
knowledge_base = None
speech_processor = None


@app.on_event("startup")
async def startup_event():
    """Initialize database and load models on startup."""
    global sales_agent, knowledge_base, speech_processor
    
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized")
        
        # Initialize knowledge base
        knowledge_base = initialize_knowledge_base()
        logger.info("Knowledge base initialized")
        
        # Initialize sales agent
        sales_agent = SalesAgent()
        logger.info("Sales agent initialized")
        
        # Initialize speech processor
        speech_processor = SpeechProcessor()
        logger.info("Speech processor initialized")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")


# ==================== Customer Endpoints ====================

@app.post("/api/customers", response_model=CustomerResponse)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer."""
    try:
        db_customer = Customer(**customer.dict())
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        logger.info(f"Customer created: {db_customer.id}")
        return db_customer
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get customer by ID."""
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/customers", response_model=list[CustomerResponse])
def get_all_customers(db: Session = Depends(get_db)):
    """Get all customers."""
    try:
        customers = db.query(Customer).all()
        return customers
    except Exception as e:
        logger.error(f"Error getting customers: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, customer: CustomerUpdate, db: Session = Depends(get_db)):
    """Update customer."""
    try:
        db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not db_customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        update_data = customer.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_customer, key, value)
        
        db.commit()
        db.refresh(db_customer)
        logger.info(f"Customer updated: {customer_id}")
        return db_customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Conversation & Chat Endpoints ====================

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Process text chat message."""
    try:
        if not sales_agent:
            raise HTTPException(status_code=503, detail="Sales agent not initialized")
        
        # Get product context from RAG
        product_context = ""
        if knowledge_base:
            product_context = knowledge_base.get_context(request.message, k=3)
        
        # Get AI response
        response = sales_agent.send_message(
            user_message=request.message,
            product_context=product_context,
            conversation_history=request.conversation_history,
        )
        
        # Save conversation if customer_id provided
        customer_id = request.customer_id
        if not customer_id and request.customer_name:
            # Try to find customer by name
            customer = db.query(Customer).filter(Customer.name == request.customer_name).first()
            if customer:
                customer_id = customer.id
        
        if customer_id:
            # Save user message
            user_conv = Conversation(
                customer_id=customer_id,
                message_type="user",
                content=request.message
            )
            db.add(user_conv)
            
            # Save assistant response
            assistant_conv = Conversation(
                customer_id=customer_id,
                message_type="assistant",
                content=response
            )
            db.add(assistant_conv)
            db.commit()
        
        # Get lead status if customer exists
        lead_status = None
        if customer_id:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                lead_status = customer.lead_status
        
        return ChatResponse(
            response=response,
            customer_id=customer_id,
            timestamp=datetime.utcnow(),
            lead_status=lead_status,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/conversations/{customer_id}", response_model=list[ConversationResponse])
def get_conversations(customer_id: int, db: Session = Depends(get_db)):
    """Get conversation history for a customer."""
    try:
        conversations = db.query(Conversation).filter(
            Conversation.customer_id == customer_id
        ).order_by(Conversation.timestamp).all()
        return conversations
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Lead Qualification Endpoints ====================

@app.post("/api/qualify-lead", response_model=LeadQualificationResponse)
def qualify_lead(request: LeadQualificationRequest, db: Session = Depends(get_db)):
    """Qualify a lead based on customer data."""
    try:
        customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Analyze sentiment
        sentiment_text = request.sentiment_text or customer.requirements or ""
        sentiment = LeadClassifier.analyze_sentiment(sentiment_text)
        
        # Calculate requirements match
        requirements = request.requirements_text or customer.requirements or ""
        recommended_text = "Professional laptop for work"  # Placeholder
        requirements_match = LeadClassifier.calculate_requirements_match(
            requirements,
            recommended_text
        )
        
        # Classify lead
        lead_status = LeadClassifier.classify_lead(
            budget=request.budget or customer.budget,
            buying_timeline=request.buying_timeline or customer.buying_timeline or "",
            requirements_match=requirements_match,
            sentiment=sentiment
        )
        
        # Update customer
        customer.lead_status = lead_status
        customer.sentiment = sentiment
        if request.budget:
            customer.budget = request.budget
        if request.buying_timeline:
            customer.buying_timeline = request.buying_timeline
        if request.requirements_text:
            customer.requirements = request.requirements_text
        
        db.commit()
        
        return LeadQualificationResponse(
            customer_id=request.customer_id,
            lead_status=lead_status,
            sentiment=sentiment,
            requirements_match=requirements_match,
            reasoning=f"Lead classified as {lead_status} based on sentiment ({sentiment}), requirements match ({requirements_match:.1f}/10), budget (${request.budget or customer.budget or 0}), and timeline ({request.buying_timeline or customer.buying_timeline or 'Not specified'})"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error qualifying lead: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Call Summary Endpoints ====================

@app.post("/api/call-summary", response_model=CallSummaryResponse)
def generate_call_summary(request: CallSummaryRequest, db: Session = Depends(get_db)):
    """Generate a summary of a customer call."""
    try:
        if not sales_agent:
            raise HTTPException(status_code=503, detail="Sales agent not initialized")
        
        customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Generate summary
        summary_text = sales_agent.generate_summary(
            conversation_history=request.conversation_history,
            customer_name=customer.name
        )
        
        # Extract key information from conversation for analysis
        all_messages = " ".join([f"{user} {assistant}" for user, assistant in request.conversation_history])
        sentiment = LeadClassifier.analyze_sentiment(all_messages)
        
        # Create call summary record
        call_summary = CallSummary(
            customer_id=request.customer_id,
            summary=summary_text,
            requirements=customer.requirements,
            budget=customer.budget,
            sentiment=sentiment,
            lead_classification=customer.lead_status,
        )
        db.add(call_summary)
        db.commit()
        db.refresh(call_summary)
        
        logger.info(f"Call summary created: {call_summary.id}")
        return call_summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating call summary: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/call-summaries/{customer_id}", response_model=list[CallSummaryResponse])
def get_call_summaries(customer_id: int, db: Session = Depends(get_db)):
    """Get all call summaries for a customer."""
    try:
        summaries = db.query(CallSummary).filter(
            CallSummary.customer_id == customer_id
        ).order_by(CallSummary.created_at.desc()).all()
        return summaries
    except Exception as e:
        logger.error(f"Error getting call summaries: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Appointment Endpoints ====================

@app.post("/api/appointments", response_model=AppointmentResponse)
def create_appointment(appointment: AppointmentCreate, db: Session = Depends(get_db)):
    """Create a new appointment."""
    try:
        db_appointment = Appointment(**appointment.dict())
        db.add(db_appointment)
        db.commit()
        db.refresh(db_appointment)
        logger.info(f"Appointment created: {db_appointment.id}")
        return db_appointment
    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/appointments/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """Get appointment by ID."""
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return appointment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting appointment: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/customers/{customer_id}/appointments", response_model=list[AppointmentResponse])
def get_customer_appointments(customer_id: int, db: Session = Depends(get_db)):
    """Get all appointments for a customer."""
    try:
        appointments = db.query(Appointment).filter(
            Appointment.customer_id == customer_id
        ).order_by(Appointment.appointment_date).all()
        return appointments
    except Exception as e:
        logger.error(f"Error getting customer appointments: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/appointments/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    appointment: AppointmentUpdate,
    db: Session = Depends(get_db)
):
    """Update appointment."""
    try:
        db_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not db_appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        update_data = appointment.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_appointment, key, value)
        
        db.commit()
        db.refresh(db_appointment)
        logger.info(f"Appointment updated: {appointment_id}")
        return db_appointment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating appointment: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/appointments", response_model=list[AppointmentResponse])
def get_all_appointments(db: Session = Depends(get_db)):
    """Get all appointments."""
    try:
        appointments = db.query(Appointment).order_by(Appointment.appointment_date).all()
        return appointments
    except Exception as e:
        logger.error(f"Error getting appointments: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Dashboard Endpoints ====================

@app.get("/api/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    try:
        total_customers = db.query(Customer).count()
        hot_leads = db.query(Customer).filter(Customer.lead_status == "Hot").count()
        warm_leads = db.query(Customer).filter(Customer.lead_status == "Warm").count()
        cold_leads = db.query(Customer).filter(Customer.lead_status == "Cold").count()
        
        scheduled_appointments = db.query(Appointment).filter(
            Appointment.status == "Scheduled"
        ).count()
        completed_appointments = db.query(Appointment).filter(
            Appointment.status == "Completed"
        ).count()
        
        # Calculate average sentiment
        conversations = db.query(Conversation).all()
        if conversations:
            sentiments = []
            for conv in conversations:
                if conv.message_type == "user":
                    sentiment = LeadClassifier.analyze_sentiment(conv.content)
                    sentiments.append(sentiment)
            
            if sentiments:
                positive_count = sum(1 for s in sentiments if s == "Positive")
                negative_count = sum(1 for s in sentiments if s == "Negative")
                
                if positive_count > negative_count:
                    average_sentiment = "Positive"
                elif negative_count > positive_count:
                    average_sentiment = "Negative"
                else:
                    average_sentiment = "Neutral"
            else:
                average_sentiment = "Neutral"
        else:
            average_sentiment = "Neutral"
        
        conversation_count = db.query(Conversation).count()
        
        return DashboardStats(
            total_customers=total_customers,
            hot_leads=hot_leads,
            warm_leads=warm_leads,
            cold_leads=cold_leads,
            scheduled_appointments=scheduled_appointments,
            completed_appointments=completed_appointments,
            average_sentiment=average_sentiment,
            conversation_count=conversation_count,
        )
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Health Check ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "agents_ready": {
            "sales_agent": sales_agent is not None,
            "knowledge_base": knowledge_base is not None,
            "speech_processor": speech_processor is not None,
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
