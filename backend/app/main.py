"""FastAPI backend for the AI Sales Voice Agent."""

import logging
import os
import io
import tempfile
import threading
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
import io
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
        
        # Get AI response with threading timeout (Windows compatible)
        try:
            ai_result = []
            ai_error = []

            def call_gemini():
                try:
                    result = sales_agent.send_message(
                        user_message=request.message,
                        product_context=product_context,
                        conversation_history=request.conversation_history,
                    )
                    ai_result.append(result)
                except Exception as e:
                    ai_error.append(str(e))

            thread = threading.Thread(target=call_gemini, daemon=True)
            thread.start()
            thread.join(timeout=10)  # 10 seconds for Gemini

            if ai_result:
                response = ai_result[0]
                logger.info("Gemini responded successfully")
            else:
                err = ai_error[0] if ai_error else "timeout"
                logger.warning(f"Gemini failed: {err}, using fallback")
                message_lower = request.message.lower()
                if any(w in message_lower for w in ["laptop", "computer", "device", "buy", "need", "looking"]):
                    response = "We have a great range of laptops! For video editing, the Dell XPS 15 with RTX 3060 and 32GB RAM is excellent at $2,499. For gaming, the ASUS ROG at $1,799 is top rated. For business, the Lenovo ThinkPad at $899 is reliable. For budget, the HP Pavilion starts at $499. What is your main use case and budget?"
                elif any(w in message_lower for w in ["price", "cost", "how much", "budget", "rupee", "inr", "thousand"]):
                    response = "Our laptops are priced for every budget. Entry level starts at around 40,000 rupees for the HP Pavilion. Mid-range ThinkPad and HP Spectre are around 70,000 to 90,000 rupees. High performance Dell XPS 15 and MacBook Pro are 1,20,000 to 1,80,000 rupees. Gaming laptops like ASUS ROG start at 85,000 rupees. What budget range works for you?"
                elif any(w in message_lower for w in ["gaming", "game", "play"]):
                    response = "For gaming, our best options are: ASUS ROG Strix with RTX 4070 at 1,40,000 rupees, Lenovo Legion 5 with RTX 3060 at 85,000 rupees, and MSI Katana with RTX 3050 at 65,000 rupees. All have high refresh rate displays and excellent cooling. What is your budget for a gaming laptop?"
                elif any(w in message_lower for w in ["video", "edit", "creative", "design", "render"]):
                    response = "For video editing, the Dell XPS 15 with RTX 3060, 32GB RAM and 4K OLED display is our top pick at 1,70,000 rupees. The MacBook Pro M2 at 1,50,000 rupees is also excellent for creative work. Both handle 4K footage smoothly. What resolution footage do you work with?"
                elif any(w in message_lower for w in ["business", "work", "office", "professional"]):
                    response = "For business use, the Lenovo ThinkPad X1 Carbon is outstanding at 95,000 rupees. It is ultra light, has 14 hour battery, and military grade durability. The HP EliteBook at 80,000 rupees is also great for professionals. Would you like to know more?"
                elif any(w in message_lower for w in ["appointment", "demo", "schedule", "book", "meet", "visit"]):
                    response = "I would love to schedule a product demo for you. We have slots available tomorrow and throughout this week. The demo takes about 30 minutes and I will show you the exact laptops matching your needs. What day and time works best for you?"
                elif any(w in message_lower for w in ["hello", "hi", "hey", "good", "how are"]):
                    response = "Hello! Welcome to TechStore. I am your AI sales assistant and I am here to help you find the perfect laptop. Whether you need it for gaming, video editing, business, or everyday use, I have got great options for every budget. What brings you in today?"
                elif any(w in message_lower for w in ["thank", "thanks", "bye", "goodbye"]):
                    response = "Thank you for choosing TechStore! It was a pleasure helping you today. Feel free to call back anytime if you have more questions. Have a great day!"
                elif any(w in message_lower for w in ["spec", "specification", "ram", "processor", "storage", "ssd", "gpu", "cpu"]):
                    response = "Our top laptops come with the latest specs. The Dell XPS 15 has Intel i7 13th gen, RTX 3060, 32GB RAM, 1TB NVMe SSD. The ASUS ROG has AMD Ryzen 9, RTX 4070, 16GB RAM, 512GB SSD. The ThinkPad has Intel i5, 16GB RAM, 512GB SSD. Which spec matters most to you?"
                else:
                    response = "That is a great point! To give you the best recommendation, could you tell me a bit more about what you need the laptop for and your budget? We have excellent options ranging from 40,000 to 2,00,000 rupees covering gaming, video editing, business, and everyday use."

        except Exception as e:
            logger.error(f"Chat error: {e}")
            response = "Thank you for your question. I want to help you find the perfect laptop. Could you tell me more about your specific needs and budget so I can give you the best recommendation?"
        
        # Save conversation if customer_id provided
        customer_id = request.customer_id
        if not customer_id and request.customer_name:
            # Try to find customer by name
            customer = db.query(Customer).filter(Customer.name == request.customer_name).first()
            if customer:
                customer_id = customer.id
        
        if customer_id:
            try:
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
            except Exception as db_error:
                logger.error(f"Database error: {db_error}")
                db.rollback()
        
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


# ==================== Voice Endpoints ====================

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio file to text."""
    try:
        if not speech_processor:
            raise HTTPException(status_code=503, detail="Speech processor not initialized")
        
        # Save uploaded file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            contents = await file.read()
            f.write(contents)
            temp_path = f.name
        
        # Transcribe
        transcription = speech_processor.speech_to_text(temp_path)
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if not transcription:
            raise HTTPException(status_code=400, detail="Failed to transcribe audio")
        
        logger.info(f"Audio transcribed: {transcription[:50]}...")
        return {"transcription": transcription}
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/text-to-speech")
async def text_to_speech(request: dict):
    """Convert text to speech."""
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text parameter required")

        logger.info(f"TTS: {text[:50]}...")

        audio_path = speech_processor.text_to_speech(text)

        if not audio_path or not os.path.exists(audio_path):
            raise HTTPException(status_code=500, detail="TTS failed")

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        try:
            os.remove(audio_path)
        except:
            pass

        logger.info(f"TTS success: {len(audio_bytes)} bytes")

        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=response.mp3"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
