import unittest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.api.deps import get_current_user_id
from app.db.base import Base
from app.db.session import DEMO_USER_ID, get_db
from app.main import app
from app.models import Call, Lead, Profile


class AnalyticsTests(unittest.TestCase):
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
        self.db.add(
            Lead(
                id="lead-analytics",
                name="A",
                email="a@x.local",
                status="qualified",
                interest_level="high",
                sentiment="positive",
                owner_id=DEMO_USER_ID,
            )
        )
        self.db.add(
            Call(
                id="call-analytics",
                lead_id="lead-analytics",
                provider="elevenlabs_exotel",
                status="completed",
                started_at=datetime.utcnow(),
                duration_seconds=90,
                call_outcome="interested",
                language="hi",
            )
        )
        self.db.commit()

        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user_id] = lambda: DEMO_USER_ID
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()

    def test_dashboard_calls_over_time_is_real(self):
        data = self.client.get("/api/v1/analytics/dashboard").json()
        self.assertEqual(len(data["calls_over_time"]["labels"]), 7)
        self.assertGreater(sum(data["calls_over_time"]["data"]), 0)

    def test_insights_include_conversion_language_and_duration(self):
        data = self.client.get("/api/v1/analytics/insights").json()
        self.assertEqual(data["conversion_rate"], 1.0)
        self.assertEqual(data["avg_call_duration_seconds"], 90)
        self.assertEqual(data["languages_breakdown"]["hi"], 1)
        self.assertEqual(data["outcomes_breakdown"]["interested"], 1)


if __name__ == "__main__":
    unittest.main()
