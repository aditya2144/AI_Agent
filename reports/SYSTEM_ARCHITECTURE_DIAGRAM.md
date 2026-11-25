# System Architecture Diagram - AI Sales Voice Agent

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐          ┌──────────────────┐            │
│  │  Web Dashboard   │          │  Voice Interface │            │
│  │  (Streamlit)     │          │  (Browser STT)   │            │
│  │                  │          │                  │            │
│  │ • Chat UI        │          │ • Microphone     │            │
│  │ • Lead Mgmt      │          │ • Speaker Output │            │
│  │ • Appointments   │          │ • Real-time      │            │
│  │ • Analytics      │          │   Interaction    │            │
│  └────────┬─────────┘          └────────┬─────────┘            │
│           │                             │                       │
│           └──────────────┬──────────────┘                       │
│                          │                                      │
└──────────────────────────┼──────────────────────────────────────┘
                           │ HTTP/REST API
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     API GATEWAY LAYER                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            FastAPI Server (Port 8000)                  │    │
│  │  • 25+ REST Endpoints                                  │    │
│  │  • Request Validation (Pydantic)                       │    │
│  │  • CORS Middleware                                     │    │
│  │  • Error Handling & Logging                            │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└──────────┬──────────────┬──────────────┬────────────────────────┘
           │              │              │
           │              │              │
    ┌──────▼──┐    ┌──────▼──┐   ┌──────▼──┐
    │  Chat   │    │  Lead   │   │Appoint- │
    │ Service │    │  Mgmt   │   │ment Mgmt│
    └──────┬──┘    └──────┬──┘   └──────┬──┘
           │              │              │
└──────────┴──────────────┴──────────────┴──────────────────────────┐
│                   BUSINESS LOGIC LAYER                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  AI Agent       │  │  RAG System  │  │ Lead Classifier  │   │
│  │  (Gemini 3.8)   │  │ (ChromaDB)   │  │  • Scoring       │   │
│  │                 │  │              │  │  • Sentiment     │   │
│  │ • Conversation  │  │ • Embeddings │  │  • Classification│   │
│  │ • Context Mgmt  │  │ • Semantic   │  │                  │   │
│  │ • Summarization │  │   Search     │  │                  │   │
│  │                 │  │ • 6 Products │  │                  │   │
│  └────────┬────────┘  └──────┬───────┘  └────────┬─────────┘   │
│           │                  │                   │               │
│           └──────────────────┼───────────────────┘               │
│                              │                                   │
│  ┌────────────────────────────▼──────────────┐                 │
│  │   Voice Processing Layer                   │                 │
│  │  ┌──────────────┐    ┌────────────────┐   │                 │
│  │  │ Whisper STT  │    │  gTTS TTS      │   │                 │
│  │  │ • Audio      │    │  • Text to     │   │                 │
│  │  │   Upload     │    │    Speech      │   │                 │
│  │  │ • Transcribe │    │  • Multiple    │   │                 │
│  │  │ • Format     │    │    Languages   │   │                 │
│  │  │   Convert    │    │                │   │                 │
│  │  └──────────────┘    └────────────────┘   │                 │
│  └────────────────────────────────────────────┘                 │
│                                                                  │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────────────┐
│                   DATA ACCESS LAYER                                │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │          SQLAlchemy ORM                                     │  │
│  │  • Connection Pooling                                       │  │
│  │  • Transaction Management                                   │  │
│  │  • Query Optimization                                       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────────────┐
│                   PERSISTENCE LAYER                                │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────────────┐  ┌───────────────────────────┐  │
│  │   SQLite Database           │  │  ChromaDB Vector Store    │  │
│  │  (sales_agent.db)           │  │  (./data/chromadb)        │  │
│  │                             │  │                           │  │
│  │  Tables:                    │  │  • Product Embeddings     │  │
│  │  • customers (5 cols)       │  │  • Semantic Vectors       │  │
│  │  • conversations (4 cols)   │  │  • Similarity Search      │  │
│  │  • appointments (6 cols)    │  │                           │  │
│  │  • call_summaries (7 cols)  │  │                           │  │
│  │  • products (11 cols)       │  │                           │  │
│  │                             │  │                           │  │
│  │  Total Records: Dynamic     │  │  Indexed: Yes             │  │
│  └─────────────────────────────┘  └───────────────────────────┘  │
│                                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

```
┌────────────────────────────────────────────────────────────────┐
│              CUSTOMER INTERACTION WORKFLOW                     │
└────────────────────────────────────────────────────────────────┘

1. INITIATION
   ┌─────────────────────────────────────────┐
   │ Customer Opens Dashboard                │
   │ (Streamlit at localhost:8501)           │
   └────────────────┬────────────────────────┘
                    │
2. AUTHENTICATION & SESSION
   ├─→ System creates session
   ├─→ Load existing customers or create new
   └─→ Initialize conversation context

3. MESSAGE INPUT
   ┌─────────────────────────────────────────┐
   │ Customer Types or Speaks Message        │
   │ • Text Input (Chat)                     │
   │ • Voice Input (Microphone → Whisper)    │
   └────────────────┬────────────────────────┘
                    │
4. SPEECH-TO-TEXT (if voice)
   ├─→ Audio → Whisper Model
   ├─→ Transcription
   └─→ Text extraction

5. API PROCESSING
   ┌──────────────────────────────────────┐
   │ POST /api/chat                       │
   │ {                                    │
   │   "customer_id": 1,                  │
   │   "message": "Need gaming laptop",   │
   │   "conversation_history": [...]      │
   │ }                                    │
   └────────────┬─────────────────────────┘
                │
6. CONTEXT RETRIEVAL (RAG)
   ├─→ Embed user message
   ├─→ Search ChromaDB
   ├─→ Retrieve top-3 products
   └─→ Format context

7. AI RESPONSE GENERATION
   ┌──────────────────────────────────┐
   │ Gemini 3.8 Flash                 │
   │ • System Prompt                  │
   │ • Conversation History           │
   │ • Product Context                │
   │ • User Message                   │
   └────────────┬─────────────────────┘
                │
                ├─→ Generate Response
                └─→ Return Text

8. LEAD QUALIFICATION
   ├─→ Extract: Budget, Timeline, Requirements
   ├─→ Analyze Sentiment
   ├─→ Calculate Match Score
   ├─→ Classify: Hot/Warm/Cold
   └─→ Update Customer Status

9. DATABASE STORAGE
   ├─→ Save User Message
   ├─→ Save Assistant Response
   ├─→ Update Customer Status
   ├─→ Update Conversation History
   └─→ Log Activity

10. TEXT-TO-SPEECH (if voice)
    ├─→ Response Text
    ├─→ gTTS Conversion
    ├─→ Audio Output
    └─→ Play in Browser

11. FRONTEND UPDATE
    ├─→ Display Response
    ├─→ Update Lead Status
    ├─→ Refresh Dashboard
    └─→ Ready for Next Input

12. OPTIONAL: APPOINTMENT BOOKING
    ┌─────────────────────────────────┐
    │ Customer: "Book Appointment"     │
    └────────────┬────────────────────┘
                 │
    ├─→ POST /api/appointments
    ├─→ Create appointment record
    ├─→ Save to database
    └─→ Confirm to customer

13. OPTIONAL: CALL SUMMARY
    ┌─────────────────────────────────┐
    │ Customer: "Generate Summary"     │
    └────────────┬────────────────────┘
                 │
    ├─→ Collect full conversation
    ├─→ Send to Gemini
    ├─→ Generate structured summary
    ├─→ Extract key insights
    ├─→ Save summary to database
    └─→ Display to customer
```

## Data Flow Architecture

```
INPUT SOURCES
    ↓
┌─────────────────────────────────────┐
│  User Input                         │
│  • Text Messages                    │
│  • Voice Input (Microphone)         │
└──────────────────┬──────────────────┘
                   │
PROCESSING PIPELINE
                   │
        ┌──────────┴──────────┐
        ↓                     ↓
   ┌─────────────┐    ┌────────────────┐
   │ STT Engine  │    │ Text Directly  │
   │ (Whisper)   │    │ (Typed Input)  │
   └──────┬──────┘    └────────┬───────┘
          └──────────┬─────────┘
                     ↓
           ┌──────────────────────┐
           │ Normalize Text       │
           │ • Clean             │
           │ • Tokenize          │
           │ • Validate          │
           └──────────┬───────────┘
                      ↓
        ┌─────────────────────────────┐
        │ RAG Context Retrieval       │
        └──────────┬──────────────────┘
                   │
        ┌──────────┴───────────┐
        ↓                      ↓
    ┌────────────┐    ┌──────────────────┐
    │ Embeddings │    │ Vector Database  │
    │ (HF Model) │    │ (ChromaDB)       │
    └────────┬───┘    └────────┬─────────┘
             └──────────┬──────┘
                        ↓
              ┌──────────────────────┐
              │ Retrieved Products   │
              │ (Top 3 Matches)      │
              └──────────┬───────────┘
                         ↓
        ┌────────────────────────────────┐
        │ AI Model Processing            │
        │ • Gemini 3.8 Flash             │
        │ • System Prompt + Context      │
        │ • Multi-turn Conversation      │
        └──────────┬─────────────────────┘
                   │
                   ├─→ Generate Response
                   ├─→ Extract Entities
                   └─→ Analyze Intent

OUTPUT GENERATION
                   │
        ┌──────────┴──────────────┐
        ↓                         ↓
   ┌──────────────┐      ┌────────────────┐
   │ Text Response│      │ Lead Status    │
   │ (AI Message) │      │ Update         │
   └──────┬───────┘      └────────┬───────┘
          │                       │
          ├──────────┬────────────┘
          │          │
          ↓          ↓
   ┌─────────────────────────────┐
   │ Database Storage            │
   │ • Conversation Record       │
   │ • Customer Update           │
   │ • Status Change             │
   └──────────────┬──────────────┘
                  │
        ┌─────────┴─────────┐
        ↓                   ↓
   ┌──────────────┐  ┌────────────────┐
   │ Text Output  │  │ Voice Output   │
   │ (Display)    │  │ (TTS → Audio)  │
   └──────────────┘  └────────────────┘
```

## Deployment Architecture (Scalable)

```
CURRENT (SINGLE SERVER)
┌────────────────────────────────────┐
│ Development Machine                │
├────────────────────────────────────┤
│ ┌──────────────────────────────┐   │
│ │ Streamlit (Port 8501)        │   │
│ │ FastAPI (Port 8000)          │   │
│ │ SQLite (sales_agent.db)      │   │
│ │ ChromaDB (data/chromadb)     │   │
│ └──────────────────────────────┘   │
└────────────────────────────────────┘
  Suitable for: Testing, MVP, Demo


SCALABLE PRODUCTION (100K USERS)
┌────────────────────────────────────────┐
│          LOAD BALANCER (ALB)           │
├────────────────────────────────────────┤
│  • Route traffic                       │
│  • SSL/TLS termination                 │
│  • Health checks                       │
└────────┬───────────────┬───────────────┘
         │               │
    ┌────▼────┐      ┌───▼────┐
    │ FastAPI │      │FastAPI │
    │Instance │      │Instance│
    │   #1    │...  │   #N   │
    └────┬────┘      └───┬────┘
         │               │
         └───────┬───────┘
                 │
        ┌────────▼────────┐
        │  API Gateway    │
        │  • Rate limit   │
        │  • Cache layer  │
        └────────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼──┐    ┌────▼────┐  ┌───▼──┐
│Redis │    │PostgreSQL   │Vector│
│Cache │    │  RDS Multi  │  DB  │
│      │    │   -AZ       │      │
└──────┘    └────────────┘ └──────┘
                 │
         ┌───────┴────────┐
         ▼                ▼
     ┌────────┐      ┌────────┐
     │S3 Logs │      │S3 Audio│
     │Archive │      │Files   │
     └────────┘      └────────┘
```

## Security & Data Flow

```
┌─────────────────────────────────────────┐
│ SECURITY LAYERS                         │
├─────────────────────────────────────────┤
│                                         │
│ 1. INPUT VALIDATION                     │
│    ├─ Pydantic schemas                  │
│    ├─ Type checking                     │
│    └─ SQL injection prevention (ORM)    │
│                                         │
│ 2. AUTHENTICATION                       │
│    ├─ API key management                │
│    └─ Environment variables             │
│                                         │
│ 3. ENCRYPTION                           │
│    ├─ HTTPS/TLS (future)                │
│    └─ Database encryption (future)      │
│                                         │
│ 4. ACCESS CONTROL                       │
│    ├─ CORS middleware                   │
│    ├─ Rate limiting (future)            │
│    └─ User permissions (future)         │
│                                         │
│ 5. AUDIT & LOGGING                      │
│    ├─ Request logging                   │
│    ├─ Error tracking                    │
│    └─ Activity logs                     │
│                                         │
└─────────────────────────────────────────┘
```

## Technology Stack Mapping

```
FRONTEND LAYER
├─ Streamlit 1.28.1
│  ├─ Dashboard UI
│  ├─ Chat Interface
│  └─ Real-time Updates

API LAYER
├─ FastAPI 0.104.1
├─ Uvicorn 0.24.0
├─ Pydantic 2.5.0
└─ SQLAlchemy 2.0.23

AI & LANGUAGE
├─ Google Gemini 3.8 Flash
├─ LangChain 0.1.0
├─ HuggingFace Embeddings
└─ TextBlob (Sentiment)

DATA MANAGEMENT
├─ SQLite 3
├─ ChromaDB 0.4.17
└─ SQLAlchemy ORM

SPEECH PROCESSING
├─ Whisper (STT)
├─ gTTS (TTS)
└─ pydub (Audio)

UTILITIES
├─ Python 3.12
├─ numpy, pandas
└─ python-dotenv
```

---

**Architecture Design Pattern:** Microservices-ready monolith with clear separation of concerns
**Deployment Pattern:** Containerizable for Kubernetes
**Data Pattern:** Event-driven, eventually consistent
**Security Pattern:** Defense in depth with multiple validation layers
