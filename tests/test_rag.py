import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.db.base import Base
from app.db.session import DEMO_USER_ID
from app.models import Profile
from app.services import rag_service


class RAGTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add(Profile(id=DEMO_USER_ID, email="demo@calleros.local"))
        self.db.commit()
        rag_service.embed = lambda texts: [rag_service._hash_embedding(t) for t in texts]

    def tearDown(self):
        self.db.close()

    def test_chunking_creates_overlapping_chunks(self):
        text = "Follow up within 24 hours. " * 80
        chunks = rag_service.chunk_text(text, size=200, overlap=50)
        self.assertGreater(len(chunks), 1)
        self.assertLessEqual(max(len(chunk) for chunk in chunks), 210)

    def test_ingest_and_search(self):
        doc = rag_service.ingest_document(
            self.db,
            DEMO_USER_ID,
            "Follow-up policy",
            "Follow up within 24 hours and reference the requirements discussed on the call.",
        )
        self.assertEqual(doc.status, "ready")
        self.assertGreaterEqual(doc.chunk_count, 1)
        results = rag_service.search("follow up within 24 hours", DEMO_USER_ID, self.db)
        self.assertTrue(results)
        self.assertEqual(results[0]["title"], "Follow-up policy")
        self.assertGreater(results[0]["relevance_score"], 0)

    def test_search_is_owner_isolated(self):
        rag_service.ingest_document(
            self.db, DEMO_USER_ID, "Private", "Secret onboarding details for ACME"
        )
        self.assertEqual(rag_service.search("secret onboarding", "other-user", self.db), [])

    def test_builtin_fallback(self):
        self.assertTrue(rag_service.builtin_search("expensive"))


if __name__ == "__main__":
    unittest.main()
