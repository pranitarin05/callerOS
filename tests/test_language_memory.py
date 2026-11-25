import asyncio
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.core.language import detect_language, resolve_language
from app.db.base import Base
from app.db.session import DEMO_USER_ID
from app.models import Lead, Profile
from app.services import memory_service


class LanguageTests(unittest.TestCase):
    def test_hindi_devanagari(self):
        self.assertEqual(detect_language("नमस्ते, क्या आप डेमो चाहते हैं?"), "hi")

    def test_hinglish_romanized(self):
        self.assertEqual(
            detect_language("Namaste aap, kya aap product demo chahte hain?"), "hinglish"
        )

    def test_english(self):
        self.assertEqual(
            detect_language("Hello, are you interested in a product demo?"), "en"
        )

    def test_preferred_language_for_short_ambiguous_text(self):
        self.assertEqual(resolve_language("yes", "hi"), "hi")
        self.assertEqual(
            resolve_language("Hello, yes please schedule a product demo for next week", "hi"),
            "en",
        )


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add(Profile(id=DEMO_USER_ID, email="demo@calleros.local"))
        self.db.commit()
        self.db.add(Lead(id="lead-mem", name="M", email="m@x.local", owner_id=DEMO_USER_ID))
        self.db.commit()

        async def fake_summarize(previous, new_text, language):
            return (previous + "\n" + new_text)[:4000]

        self.original = memory_service.summarize_memory
        memory_service.summarize_memory = fake_summarize

    def tearDown(self):
        memory_service.summarize_memory = self.original
        self.db.close()

    def test_memory_accumulates_and_tracks_language(self):
        qualification = {
            "requirements": "Automate follow-ups",
            "interest": "high",
            "sentiment": "positive",
            "call_outcome": "interested",
            "next_action": "Schedule demo",
        }
        asyncio.run(
            memory_service.update_memory(
                self.db, "lead-mem", "wants a demo", "Interested", qualification, "hinglish"
            )
        )
        record = memory_service.get_memory(self.db, "lead-mem")
        self.assertIsNotNone(record)
        self.assertEqual(record.language, "hinglish")
        self.assertIn("Automate follow-ups", record.summary)
        context = memory_service.get_memory_context(self.db, "lead-mem")
        self.assertIn("Previous conversation context", context)


if __name__ == "__main__":
    unittest.main()
