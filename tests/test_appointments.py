import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.core.config import settings
from app.db.base import Base
from app.db.session import DEMO_USER_ID
from app.models import Lead, Profile
from app.services import appointment_service


class AppointmentTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add(Profile(id=DEMO_USER_ID, email="demo@calleros.local"))
        self.db.commit()
        self.db.add(
            Lead(
                id="lead-apt",
                name="Apt Lead",
                email="apt@example.com",
                owner_id=DEMO_USER_ID,
            )
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_slots_follow_business_hours(self):
        slots = appointment_service.get_available_slots(self.db, DEMO_USER_ID, days=2)
        self.assertTrue(slots)
        self.assertEqual(len(slots), len(set(slots)))
        first = appointment_service.parse_datetime(slots[0])
        local = first.replace(tzinfo=__import__("datetime").timezone.utc).astimezone(
            appointment_service._local_timezone()
        )
        self.assertGreaterEqual(local.hour, settings.business_hours_start)

    def test_booking_and_conflict(self):
        slots = appointment_service.get_available_slots(self.db, DEMO_USER_ID, days=2)
        first = slots[0]
        booked = appointment_service.book_appointment(
            self.db, DEMO_USER_ID, "lead-apt", first
        )
        self.assertIsNotNone(booked)
        self.assertEqual(booked["status"], "scheduled")
        self.assertFalse(
            appointment_service.is_slot_available(
                self.db, DEMO_USER_ID, appointment_service.parse_datetime(first)
            )
        )
        other = appointment_service.book_appointment(
            self.db, "someone-else", "lead-apt", slots[1]
        )
        self.assertIsNone(other)

    def test_past_slot_rejected(self):
        past = (datetime.utcnow() - timedelta(days=1)).isoformat()
        self.assertIsNone(
            appointment_service.book_appointment(self.db, DEMO_USER_ID, "lead-apt", past)
        )


if __name__ == "__main__":
    unittest.main()
