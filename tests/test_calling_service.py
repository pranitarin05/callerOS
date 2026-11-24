import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401 - register tables
from app.core.config import settings
from app.db.base import Base
from app.db.session import DEMO_USER_ID
from app.models import Call, CallSummary, Lead, Profile
from app.services import calling_service


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = ""

    def json(self):
        return self._payload


class FakeAsyncClient:
    last_payload = None
    last_headers = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, headers=None, json=None):
        FakeAsyncClient.last_payload = json
        FakeAsyncClient.last_headers = headers
        return FakeResponse(
            {
                "success": True,
                "message": "submitted",
                "conversation_id": "conv_test_123",
                "callSid": "exotel_sid_123",
            }
        )


def make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(
        Profile(id=DEMO_USER_ID, email="demo@calleros.local", full_name="Demo", is_active=True)
    )
    session.commit()
    return session


class PhoneValidationTests(unittest.TestCase):
    def test_indian_number_is_normalized(self):
        self.assertEqual(
            calling_service.normalize_phone_number("9876543210"),
            "+919876543210",
        )

    def test_formatted_number_is_normalized(self):
        self.assertEqual(
            calling_service.normalize_phone_number("+91 98765-43210"),
            "+919876543210",
        )

    def test_invalid_number_rejected(self):
        with self.assertRaises(HTTPException):
            calling_service.normalize_phone_number("123")


class CallingConfigTests(unittest.TestCase):
    def test_config_reports_provider(self):
        config = calling_service.calling_config()
        self.assertEqual(config["provider"], "elevenlabs_exotel")
        self.assertIn("groq_configured", config)


class OutboundCallTests(unittest.TestCase):
    def setUp(self):
        self.db = make_db()
        self.lead = Lead(
            id="lead-test-1",
            name="Test Prospect",
            email="test@example.com",
            phone="+919876543210",
            status="new",
            owner_id=DEMO_USER_ID,
        )
        self.db.add(self.lead)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_live_call_uses_official_payload_and_persists_call(self):
        with patch.object(settings, "elevenlabs_api_key", "test-key"), patch.object(
            settings, "elevenlabs_agent_id", "test-agent"
        ), patch.object(
            settings, "elevenlabs_phone_number_id", "test-number"
        ), patch.object(
            calling_service.httpx, "AsyncClient", FakeAsyncClient
        ):
            result = asyncio.run(
                calling_service.initiate_call(
                    self.db,
                    DEMO_USER_ID,
                    "9876543210",
                    self.lead.id,
                    "Test Prospect",
                    "live",
                )
            )

        self.assertTrue(result["success"])
        self.assertFalse(result["simulated"])
        self.assertEqual(result["conversation_id"], "conv_test_123")
        self.assertEqual(result["exotel_call_sid"], "exotel_sid_123")

        payload = FakeAsyncClient.last_payload
        self.assertEqual(payload["agent_id"], "test-agent")
        self.assertEqual(payload["agent_phone_number_id"], "test-number")
        self.assertEqual(payload["to_number"], "+919876543210")
        self.assertEqual(
            payload["conversation_initiation_client_data"]["source_info"]["source"],
            "exotel",
        )
        self.assertIn(
            "call_id",
            payload["conversation_initiation_client_data"]["dynamic_variables"],
        )

        call = self.db.query(Call).filter(Call.id == result["call_id"]).first()
        self.assertIsNotNone(call)
        self.assertEqual(call.provider, "elevenlabs_exotel")
        self.assertEqual(call.status, "initiated")

    def test_duplicate_call_is_prevented(self):
        with patch.object(settings, "elevenlabs_api_key", "test-key"), patch.object(
            settings, "elevenlabs_agent_id", "test-agent"
        ), patch.object(
            settings, "elevenlabs_phone_number_id", "test-number"
        ), patch.object(
            calling_service.httpx, "AsyncClient", FakeAsyncClient
        ):
            asyncio.run(
                calling_service.initiate_call(
                    self.db, DEMO_USER_ID, "9876543210", self.lead.id, mode="live"
                )
            )
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(
                    calling_service.initiate_call(
                        self.db, DEMO_USER_ID, "9876543210", self.lead.id, mode="live"
                    )
                )
        self.assertEqual(ctx.exception.status_code, 409)


class WebhookTests(unittest.TestCase):
    def setUp(self):
        self.db = make_db()
        self.lead = Lead(
            id="lead-webhook-1",
            name="Webhook Lead",
            email="webhook@example.com",
            phone="+919876543210",
            status="new",
            owner_id=DEMO_USER_ID,
        )
        self.db.add(self.lead)
        self.db.commit()
        self.call = Call(
            id="call-webhook-1",
            lead_id=self.lead.id,
            provider="elevenlabs_exotel",
            conversation_id="conv_webhook_1",
            status="initiated",
            initiation_status="submitted",
            phone_number="+919876543210",
        )
        self.db.add(self.call)
        self.db.commit()

        self.payload = {
            "type": "post_call_transcription",
            "data": {
                "conversation_id": "conv_webhook_1",
                "status": "done",
                "transcript": [
                    {"role": "agent", "message": "Hello, this is an AI assistant."},
                    {"role": "user", "message": "Yes, we need help and a demo soon."},
                ],
                "analysis": {
                    "call_successful": "success",
                    "transcript_summary": "Interested prospect requested a demo.",
                    "data_collection_results": {},
                },
                "metadata": {"call_duration_secs": 45, "start_time_unix_secs": 1700000000},
                "conversation_initiation_client_data": {
                    "dynamic_variables": {
                        "call_id": self.call.id,
                        "lead_id": self.lead.id,
                    }
                },
            },
        }

        async def fake_generation(text, fallback):
            return fallback

        self.generation_patch = patch.object(
            calling_service, "generate_qualification", new=fake_generation
        )
        self.generation_patch.start()

    def tearDown(self):
        self.generation_patch.stop()
        self.db.close()

    def test_webhook_processing_is_idempotent(self):
        first = asyncio.run(calling_service.process_webhook(self.payload, self.db))
        second = asyncio.run(calling_service.process_webhook(self.payload, self.db))

        self.assertEqual(first["status"], "processed")
        self.assertEqual(second["status"], "already_processed")
        self.assertEqual(self.db.query(CallSummary).filter(CallSummary.call_id == self.call.id).count(), 1)

        self.db.refresh(self.call)
        self.assertEqual(self.call.status, "completed")
        self.assertEqual(self.call.duration_seconds, 45)

    def test_missing_webhook_secret_is_rejected(self):
        with patch.object(settings, "elevenlabs_webhook_secret", ""):
            with self.assertRaises(HTTPException) as ctx:
                calling_service.verify_webhook(b"{}", "signature")
        self.assertEqual(ctx.exception.status_code, 503)

    def test_webhook_signature_uses_official_sdk(self):
        class FakeClient:
            def __init__(self, api_key=None):
                self.webhooks = SimpleNamespace(
                    construct_event=lambda rawBody, sig_header, secret: {
                        "type": "post_call_transcription",
                        "data": {},
                    }
                )

        with patch.object(settings, "elevenlabs_webhook_secret", "test-secret"), patch(
            "elevenlabs.client.ElevenLabs", FakeClient
        ):
            event = calling_service.verify_webhook(b"{}", "test-signature")
        self.assertEqual(event["type"], "post_call_transcription")


if __name__ == "__main__":
    unittest.main()
