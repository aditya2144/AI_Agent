# System Architecture - AI Sales Voice Agent

## Overview

The AI Sales Voice Agent is a full-stack conversational AI application designed for lead generation, qualification, and appointment booking. The system uses a modular architecture with clear separation of concerns.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                          │
│                   (Streamlit Web App)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Dashboard | Chat | Leads | Appointments | Analytics  │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────┬──────────────────────────────────────────────┘
               │ HTTP/REST API
┌──────────────▼──────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Chat Routes | Leads | Appointments | Analytics        │ │
│  └────────────────────────────────────────────────────────┘ │
└─┬─────────────┬─────────────┬──────────────┬────────────────┘
  │             │             │              │
  │             │             │              │
┌─▼──────────┐┌─▼──────────┐┌─▼────────────┐┌─▼──────────────┐
│   AI Agent │││  RAG      │││   Voice     ││  Lead Qual.   │
│  (Gemini)  ││ (ChromaDB) ││ (Whisper)   ││  Classifier   │
├────────────┤├───────────┤├────────────┤├───────────────┤
│ Streaming  ││ Embeddings││ STT/TTS    ││ Sentiment     │
│ Chat       ││ Vector DB ││ Audio Proc ││ Classification│
│ Summaries  ││ Product   ││ Format Conv││ Timeline      │
│            ││ Knowledge ││            ││ Budget Match  │
└────────────┘└───────────┘└────────────┘└───────────────┘
       │             │            │              │
       └─────────────┼────────────┼──────────────┘
                     │
        ┌────────────▼─────────────┐
        │   Data Access Layer      │
        │      (SQLAlchemy)        │
        ├─────────────────────────┤
        │ ORM Models & Queries    │
        │ Transaction Management  │
        │ Connection Pooling      │
        └────────────┬────────────┘
                     │
        ┌────────────▼─────────────┐
        │   Database Layer         │
        │       (SQLite)           │
        ├─────────────────────────┤
        │ Customers               │
        │ Conversations           │
        │ Appointments            │
        │ Call Summaries          │
        │ Products                │
        └────────────┬────────────┘
                     │
        ┌────────────▼─────────────┐
        │  External Services       │
        ├─────────────────────────┤
        │ Google Gemini API       │
        │ OpenAI Whisper          │
        │ Google TTS              │
        │ Sentence Transformers   │
        └─────────────────────────┘
```

## Component Details

### 1. Frontend Layer (Streamlit)

**File:** `frontend/app.py`

Responsibilities:
- Dashboard with real-time statistics
- Chat interface for conversations
- Lead management and filtering
- Appointment scheduling UI
- Call summary viewing
- Analytics and reporting

Features:
- Responsive design
- Real-time updates
- Quick action buttons
- Interactive charts
- Customer filtering

### 2. API Layer (FastAPI)

**File:** `backend/app/main.py`

Provides REST endpoints:

**Customer Management:**
- `POST /api/customers` - Create customer
- `GET /api/customers` - List customers
- `GET /api/customers/{id}` - Get customer
- `PUT /api/customers/{id}` - Update customer

**Chat & Conversation:**
- `POST /api/chat` - Send message
- `GET /api/conversations/{customer_id}` - Get history

**Lead Qualification:**
- `POST /api/qualify-lead` - Classify lead

**Appointments:**
- `POST /api/appointments` - Create appointment
- `GET /api/appointments` - List appointments
- `PUT /api/appointments/{id}` - Update appointment

**Call Summaries:**
- `POST /api/call-summary` - Generate summary
- `GET /api/call-summaries/{customer_id}` - Get summaries

**Dashboard:**
- `GET /api/dashboard/stats` - Get statistics

### 3. AI Agent Module

**File:** `backend/app/agents/sales_agent.py`

**Class:** `SalesAgent`

Functionality:
- Powered by Google Gemini API
- System prompt for sales context
- Multi-turn conversation handling
- Context preservation
- Call summary generation
- Graceful error handling

Key Methods:
- `send_message()` - Process user input and generate response
- `generate_summary()` - Create conversation summary
- `clear_history()` - Reset conversation

### 4. RAG (Retrieval-Augmented Generation)

**Files:**
- `backend/app/rag/knowledge_base.py` - Vector store management
- `backend/app/rag/product_loader.py` - Product data loading

**Technology:** LangChain + ChromaDB + HuggingFace Embeddings

Functionality:
- Semantic search over product database
- Embedding generation using `sentence-transformers`
- Persistent vector storage
- Context retrieval for AI responses

Data Flow:
```
Product Data
    ↓
Embeddings Generated (HuggingFace)
    ↓
Stored in ChromaDB
    ↓
User Query
    ↓
Similarity Search
    ↓
Top K Results Retrieved
    ↓
Passed to AI Agent
```

### 5. Lead Qualification Module

**File:** `backend/app/lead_qualification/classifier.py`

**Class:** `LeadClassifier`

Scoring System:
```
Budget          : 0-3 points
Timeline        : 0-3 points
Requirements    : 0-2 points
Sentiment       : -2 to +2 points
─────────────────────────────
Total           : 0-10 scale

Hot   : Score ≥ 7
Warm  : Score ≥ 4
Cold  : Score < 4
```

Methods:
- `classify_lead()` - Determine lead quality
- `analyze_sentiment()` - TextBlob-based analysis
- `calculate_requirements_match()` - Keyword matching

### 6. Voice Processing Module

**File:** `backend/app/voice/speech_processor.py`

**Class:** `SpeechProcessor`

Capabilities:
- **Speech-to-Text:** OpenAI Whisper model
- **Text-to-Speech:** Google Text-to-Speech (gTTS)
- **Format Conversion:** Audio format handling
- **Duration Calculation:** Audio length in seconds

Methods:
- `speech_to_text()` - Transcribe audio files
- `text_to_speech()` - Generate speech from text
- `convert_audio_format()` - Format conversion
- `get_audio_duration()` - Duration calculation

### 7. Appointment Management

**File:** `backend/app/appointments/manager.py`

**Class:** `AppointmentManager`

Operations:
- Create appointments
- Retrieve appointments
- Update status
- Cancel appointments
- Query by customer or date

Database Model:
```python
Appointment
├── id (Primary Key)
├── customer_id (Foreign Key)
├── appointment_date
├── reason
├── status (Scheduled/Completed/Cancelled)
├── notes
├── created_at
└── updated_at
```

### 8. Database Layer

**Files:**
- `backend/app/database/models.py` - SQLAlchemy models
- `backend/app/database/database.py` - Connection management

**Models:**

```python
Customer
├── id
├── name
├── email
├── phone
├── budget
├── requirements
├── buying_timeline
├── lead_status
├── sentiment
├── created_at
└── updated_at

Conversation
├── id
├── customer_id
├── message_type (user/assistant)
├── content
└── timestamp

Appointment
├── id
├── customer_id
├── appointment_date
├── reason
├── status
├── notes
├── created_at
└── updated_at

CallSummary
├── id
├── customer_id
├── summary
├── requirements
├── budget
├── sentiment
├── lead_classification
├── duration_seconds
└── created_at

Product
├── id
├── name
├── model
├── price
├── processor
├── ram
├── storage
├── display
├── gpu
├── battery_life
├── weight
├── description
├── stock
└── created_at
```

### 9. Data Models (Pydantic Schemas)

**File:** `backend/app/models/schemas.py`

Provides type validation for all API requests/responses:
- CustomerCreate, CustomerResponse, CustomerUpdate
- ChatRequest, ChatResponse
- AppointmentCreate, AppointmentResponse
- CallSummaryRequest, CallSummaryResponse
- LeadQualificationRequest, LeadQualificationResponse
- DashboardStats

## Data Flow Diagrams

### Chat Flow
```
User Input (Text)
    ↓
API Endpoint (/chat)
    ↓
RAG: Retrieve Product Context
    ↓
AI Agent: Process Message
    ↓
Database: Save Conversation
    ↓
Response to Frontend
    ↓
Display in Chat UI
```

### Lead Qualification Flow
```
Customer Interaction
    ↓
Collect: Budget, Timeline, Requirements
    ↓
Analyze: Sentiment
    ↓
Calculate: Requirements Match
    ↓
Classification Algorithm
    ↓
Update Lead Status
    ↓
Display on Dashboard
```

### Appointment Flow
```
Customer Requests Appointment
    ↓
AI Agent Collects: Date, Time, Reason
    ↓
Create Appointment Record
    ↓
Save to Database
    ↓
Update Customer Timeline
    ↓
Confirm to Customer
    ↓
Display on Calendar
```

## Deployment Architecture

### Local Development
```
Developer Machine
├── Python 3.9+
├── SQLite Database
├── ChromaDB (Local)
├── FastAPI Backend (Port 8000)
└── Streamlit Frontend (Port 8501)
```

### Production (Single Server)
```
Production Server
├── Python Environment
├── PostgreSQL Database (replaces SQLite)
├── ChromaDB Persistence
├── FastAPI (Uvicorn)
├── Nginx Reverse Proxy
└── Systemd Services
```

### Scaled Production (100K Users)
```
Load Balancer (ALB)
    ├── FastAPI Instance 1
    ├── FastAPI Instance 2
    ├── FastAPI Instance 3
    └── FastAPI Instance N
         ↓
    API Gateway
         ├─────── Cache Layer (Redis)
         ├─────── Message Queue (RabbitMQ)
         ├─────── Database (PostgreSQL RDS)
         ├─────── Vector DB (Distributed)
         └─────── External APIs
```

## Security Considerations

### API Security
- CORS middleware configured
- Input validation via Pydantic
- Error handling prevents info leakage
- API keys stored in environment variables

### Database Security
- SQLAlchemy ORM prevents SQL injection
- Password hashing (future enhancement)
- Role-based access control (future)
- Audit logging (future)

### External API Security
- API keys in .env (not committed)
- Secrets management ready
- Error messages sanitized
- Rate limiting ready

## Performance Characteristics

### Response Times (Target)
- Chat: < 2 seconds
- Lead Qualification: < 500ms
- Product Search: < 200ms
- Database Query: < 50ms

### Scalability Metrics
- Database connections: Pooling (10-50)
- Concurrent users: 100-1000 (single server)
- Requests per second: 100-500 (single server)
- Data retention: Unlimited (SSD storage)

### Resource Usage
- RAM: 2-4 GB (single server)
- CPU: 2-4 cores
- Disk: 100 GB (includes embeddings)
- Network: 10 Mbps+ recommended

## Monitoring & Logging

### Application Logs
- Location: `logs/` directory
- Format: JSON structured logging
- Levels: DEBUG, INFO, WARNING, ERROR
- Rotation: Daily (future)

### Metrics to Track
- API response times
- Database query times
- Error rates
- User session duration
- Conversation count
- Lead conversion rate

## Error Handling

All components implement:
- Try-catch blocks
- Logging of errors
- User-friendly error messages
- Graceful degradation
- Automatic retry logic (future)

## Extension Points

Future enhancements can be added:
- Multi-language support (Translate API)
- Video conferencing (WebRTC)
- Email notifications (SendGrid)
- SMS alerts (Twilio)
- Payment integration (Stripe)
- CRM integration (Salesforce API)
- Advanced analytics (BI tools)
- Mobile app (React Native)

---

This architecture provides a solid foundation for the AI Sales Voice Agent MVP with clear pathways for scaling to production and adding advanced features.
