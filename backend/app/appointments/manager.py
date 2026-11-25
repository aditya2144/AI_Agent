"""Appointment booking management."""

import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from app.database.models import Appointment

logger = logging.getLogger(__name__)


class AppointmentManager:
    """Manage appointment bookings."""
    
    @staticmethod
    def create_appointment(
        db: Session,
        customer_id: int,
        appointment_date: datetime,
        reason: str = "Product Consultation",
        notes: str = "",
    ) -> Optional[Appointment]:
        """Create a new appointment.
        
        Args:
            db: Database session.
            customer_id: Customer ID.
            appointment_date: Appointment date and time.
            reason: Reason for appointment.
            notes: Additional notes.
            
        Returns:
            Created Appointment object or None if error.
        """
        try:
            appointment = Appointment(
                customer_id=customer_id,
                appointment_date=appointment_date,
                reason=reason,
                status="Scheduled",
                notes=notes,
            )
            db.add(appointment)
            db.commit()
            db.refresh(appointment)
            
            logger.info(f"Appointment created: {appointment.id}")
            return appointment
            
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def get_appointment(db: Session, appointment_id: int) -> Optional[Appointment]:
        """Get appointment by ID.
        
        Args:
            db: Database session.
            appointment_id: Appointment ID.
            
        Returns:
            Appointment object or None.
        """
        try:
            return db.query(Appointment).filter(Appointment.id == appointment_id).first()
        except Exception as e:
            logger.error(f"Error getting appointment: {e}")
            return None
    
    @staticmethod
    def get_customer_appointments(db: Session, customer_id: int) -> List[Appointment]:
        """Get all appointments for a customer.
        
        Args:
            db: Database session.
            customer_id: Customer ID.
            
        Returns:
            List of Appointment objects.
        """
        try:
            return db.query(Appointment).filter(Appointment.customer_id == customer_id).all()
        except Exception as e:
            logger.error(f"Error getting customer appointments: {e}")
            return []
    
    @staticmethod
    def update_appointment(
        db: Session,
        appointment_id: int,
        **kwargs
    ) -> Optional[Appointment]:
        """Update appointment details.
        
        Args:
            db: Database session.
            appointment_id: Appointment ID.
            **kwargs: Fields to update.
            
        Returns:
            Updated Appointment object or None.
        """
        try:
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            if not appointment:
                return None
            
            for key, value in kwargs.items():
                if hasattr(appointment, key):
                    setattr(appointment, key, value)
            
            db.commit()
            db.refresh(appointment)
            
            logger.info(f"Appointment updated: {appointment_id}")
            return appointment
            
        except Exception as e:
            logger.error(f"Error updating appointment: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def cancel_appointment(db: Session, appointment_id: int) -> Optional[Appointment]:
        """Cancel an appointment.
        
        Args:
            db: Database session.
            appointment_id: Appointment ID.
            
        Returns:
            Updated Appointment object or None.
        """
        return AppointmentManager.update_appointment(
            db,
            appointment_id,
            status="Cancelled"
        )
    
    @staticmethod
    def get_all_appointments(db: Session) -> List[Appointment]:
        """Get all appointments.
        
        Args:
            db: Database session.
            
        Returns:
            List of all Appointment objects.
        """
        try:
            return db.query(Appointment).all()
        except Exception as e:
            logger.error(f"Error getting all appointments: {e}")
            return []
