import asyncio
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.api.deps import get_current_user_id
from app.db.base import Base
from app.db.session import DEMO_USER_ID, get_db
from app.main import app
from app.models import Profile
from app.services import agent_config_service


class AgentConfigTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add(Profile(id=DEMO_USER_ID, email="demo@calleros.local"))
        self.db.commit()

        async def fake_defaults():
            return {
                "instructions": "Default prompt",
                "first_message": "Default hello",
                "language": "hi",
            }

        self.defaults_patch = patch.object(
            agent_config_service, "fetch_elevenlabs_defaults", new=fake_defaults
        )
        self.defaults_patch.start()

        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user_id] = lambda: DEMO_USER_ID
        self.client = TestClient(app)

    def tearDown(self):
        self.defaults_patch.stop()
        app.dependency_overrides.clear()
        self.db.close()

    def test_no_override_by_default(self):
        self.assertIsNone(agent_config_service.get_override(self.db, DEMO_USER_ID))
        data = self.client.get("/api/v1/agent-config").json()
        self.assertFalse(data["customized"])
        self.assertEqual(data["defaults"]["first_message"], "Default hello")

    def test_save_and_get_override(self):
        result = self.client.put(
            "/api/v1/agent-config",
            json={
                "instructions": "You are Caller OS.",
                "first_message": "Hello {{prospect_name}}",
                "language": "en",
            },
        )
        self.assertEqual(result.status_code, 200)
        override = agent_config_service.get_override(self.db, DEMO_USER_ID)
        self.assertEqual(override["agent"]["first_message"], "Hello {{prospect_name}}")
        self.assertEqual(override["agent"]["prompt"]["prompt"], "You are Caller OS.")
        self.assertEqual(override["agent"]["language"], "en")

    def test_auto_language_is_not_overridden(self):
        agent_config_service.save_config(
            self.db,
            DEMO_USER_ID,
            instructions="Prompt",
            first_message="Hello",
            language="auto",
        )
        override = agent_config_service.get_override(self.db, DEMO_USER_ID)
        self.assertNotIn("language", override["agent"])

    def test_reset_removes_override(self):
        self.client.put(
            "/api/v1/agent-config",
            json={"instructions": "Prompt", "first_message": "Hello", "language": "en"},
        )
        response = self.client.delete("/api/v1/agent-config")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(agent_config_service.get_override(self.db, DEMO_USER_ID))

    def test_outbound_payload_contains_override(self):
        agent_config_service.save_config(
            self.db,
            DEMO_USER_ID,
            instructions="Custom prompt",
            first_message="Custom hello",
            language="en",
        )
        from app.services.calling_service import initiate_call
        from unittest.mock import patch as mock_patch

        self.db.add(
            models.Lead(
                id="lead-script",
                name="Lead",
                email="lead@example.com",
                phone="+919876543210",
                owner_id=DEMO_USER_ID,
            )
        )
        self.db.commit()

        class FakeResponse:
            status_code = 200
            text = ""

            def json(self):
                return {"success": True, "conversation_id": "conv-1", "callSid": "sid-1"}

        class FakeClient:
            last_payload = None

            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def post(self, url, headers=None, json=None):
                FakeClient.last_payload = json
                return FakeResponse()

        from app.core.config import settings
        from app.services import calling_service

        with mock_patch.object(settings, "elevenlabs_api_key", "k"), mock_patch.object(
            settings, "elevenlabs_agent_id", "a"
        ), mock_patch.object(settings, "elevenlabs_phone_number_id", "p"), mock_patch.object(
            calling_service.httpx, "AsyncClient", FakeClient
        ):
            asyncio.run(
                initiate_call(
                    self.db,
                    DEMO_USER_ID,
                    "9876543210",
                    "lead-script",
                    "Lead",
                    "live",
                )
            )

        client_data = FakeClient.last_payload["conversation_initiation_client_data"]
        self.assertIn("conversation_config_override", client_data)
        self.assertEqual(
            client_data["conversation_config_override"]["agent"]["first_message"],
            "Custom hello",
        )


if __name__ == "__main__":
    unittest.main()
