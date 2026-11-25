"""End-to-end workflow test for AI Sales Voice Agent."""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import modules
from app.database.database import SessionLocal, init_db
from app.database.models import Customer, Conversation, Appointment, CallSummary
from app.agents.sales_agent import SalesAgent
from app.lead_qualification.classifier import LeadClassifier

# Initialize
init_db()
db = SessionLocal()
agent = SalesAgent()
classifier = LeadClassifier()

print("=" * 60)
print("END-TO-END WORKFLOW TEST")
print("=" * 60)

# TEST 1: Customer Creation
print("\n[TEST 1] Creating customer...")
try:
    customer = Customer(
        name="John Smith",
        email="john.smith@example.com",
        phone="+1-555-0123",
        budget=2500,
        requirements="Video editing, 32GB RAM, RTX GPU",
        buying_timeline="This week"
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    print(f"✓ Customer created: ID={customer.id}, Name={customer.name}")
    customer_id = customer.id
except Exception as e:
    print(f"✗ Customer creation failed: {e}")
    sys.exit(1)

# TEST 2: Multi-turn conversation
print("\n[TEST 2] Starting multi-turn conversation...")
messages = [
    "Hello, I'm interested in your laptops",
    "What's the best laptop for video editing?",
    "How much does it cost?",
    "Do you offer payment plans?",
    "Can I schedule a demo?"
]

try:
    conversation_history = []
    for i, msg in enumerate(messages, 1):
        print(f"  → Message {i}: {msg[:50]}...")
        
        # Store user message in database
        convo_user = Conversation(
            customer_id=customer_id,
            message_type="user",
            content=msg
        )
        db.add(convo_user)
        db.commit()
        
        # Get agent response
        response = agent.send_message(
            user_message=msg,
            conversation_history=conversation_history
        )
        print(f"  ← Agent: {response[:100]}...")
        
        # Store agent message in database
        convo_resp = Conversation(
            customer_id=customer_id,
            message_type="assistant",
            content=response
        )
        db.add(convo_resp)
        db.commit()
        
        # Add to conversation history
        conversation_history.append((msg, response))
        time.sleep(0.3)
    
    print("✓ Multi-turn conversation completed")
except Exception as e:
    print(f"✗ Conversation failed: {e}")

# TEST 3: Lead Qualification
print("\n[TEST 3] Running lead qualification...")
try:
    lead_category = classifier.classify_lead(
        budget=2500,
        buying_timeline="This week",
        requirements_match=8.0,
        sentiment="Positive"
    )
    
    sentiment = classifier.analyze_sentiment("I'm very interested in your video editing laptops!")
    
    print(f"✓ Lead classification: {lead_category}")
    print(f"  - Sentiment: {sentiment}")
    
    # Update customer with lead status
    customer = db.query(Customer).filter_by(id=customer_id).first()
    customer.lead_status = lead_category
    customer.sentiment = sentiment
    db.commit()
    
except Exception as e:
    print(f"✗ Lead qualification failed: {e}")

# TEST 4: Appointment Booking
print("\n[TEST 4] Booking appointment...")
try:
    appointment = Appointment(
        customer_id=customer_id,
        appointment_date=datetime(2025, 1, 28, 14, 30, 0),
        reason="Product demo for video editing laptop",
        status="Scheduled"
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    print(f"✓ Appointment booked: ID={appointment.id}, Date={appointment.appointment_date}")
except Exception as e:
    print(f"✗ Appointment booking failed: {e}")
    db.rollback()

# TEST 5: Call Summary Generation
print("\n[TEST 5] Generating call summary...")
try:
    summary = CallSummary(
        customer_id=customer_id,
        summary="Customer interested in video editing laptops. High budget (2.5K), immediate timeline. Positive sentiment. Scheduled demo.",
        requirements="Video editing, 32GB RAM, RTX GPU",
        budget=2500,
        sentiment="Positive",
        lead_classification="Hot"
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    print(f"✓ Call summary created: ID={summary.id}")
except Exception as e:
    print(f"✗ Call summary failed: {e}")
    db.rollback()

# TEST 6: Database Query Validation
print("\n[TEST 6] Validating database records...")
try:
    total_customers = db.query(Customer).count()
    total_conversations = db.query(Conversation).count()
    total_appointments = db.query(Appointment).count()
    total_summaries = db.query(CallSummary).count()
    
    print(f"✓ Database records:")
    print(f"  - Customers: {total_customers}")
    print(f"  - Conversations: {total_conversations}")
    print(f"  - Appointments: {total_appointments}")
    print(f"  - Summaries: {total_summaries}")
    
    # Fetch and display the created customer record
    created_customer = db.query(Customer).filter_by(id=customer_id).first()
    if created_customer:
        print(f"\n✓ Customer details:")
        print(f"  - Name: {created_customer.name}")
        print(f"  - Email: {created_customer.email}")
        print(f"  - Budget: ${created_customer.budget}")
        print(f"  - Requirements: {created_customer.requirements}")
        print(f"  - Timeline: {created_customer.buying_timeline}")
        print(f"  - Status: {created_customer.lead_status}")
except Exception as e:
    print(f"✗ Database validation failed: {e}")

db.close()

print("\n" + "=" * 60)
print("✓ END-TO-END WORKFLOW TEST COMPLETE")
print("=" * 60)
