"""
Tests cho Telemetry API endpoints.
Chạy: cd backend && python -m pytest tests/test_telemetry.py -v
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from models import TelemetryData, Zone, User, CropSetting
from schemas import TelemetryHistoryQuery


# ── Test fixtures ──────────────────────────────────────────

@pytest.fixture(scope="module")
def test_db():
    """Tạo in-memory SQLite database cho testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # Dependency override
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    yield engine, TestingSessionLocal, override_get_db

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db):
    """Trả về một session test sạch."""
    _, SessionLocal, _ = test_db
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_zone(db_session):
    """Tạo zone mẫu."""
    zone = Zone(name="Test Zone", description="Zone for testing")
    db_session.add(zone)
    db_session.commit()
    db_session.refresh(zone)
    return zone


@pytest.fixture
def sample_user(db_session):
    """Tạo user mẫu."""
    from auth import get_password_hash
    user = User(
        username="testuser",
        hashed_password=get_password_hash("testpass123"),
        name="Test User",
        role="ADMIN"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ── TelemetryData Model Tests ─────────────────────────────

class TestTelemetryDataModel:
    """Test cho model TelemetryData."""

    def test_create_telemetry(self, db_session, sample_zone):
        """Tạo telemetry data thành công."""
        telemetry = TelemetryData(
            zone_id=sample_zone.id,
            temperature=25.5,
            humidity=60.0,
            light=500.0,
            measured_at=datetime.now(timezone.utc),
        )
        db_session.add(telemetry)
        db_session.commit()
        db_session.refresh(telemetry)

        assert telemetry.id is not None
        assert telemetry.zone_id == sample_zone.id
        assert telemetry.temperature == 25.5
        assert telemetry.humidity == 60.0
        assert telemetry.light == 500.0

    def test_create_telemetry_nullable_fields(self, db_session, sample_zone):
        """Tạo telemetry với trường nullable."""
        telemetry = TelemetryData(
            zone_id=sample_zone.id,
            temperature=25.5,
            humidity=None,
            light=None,
            measured_at=datetime.now(timezone.utc),
        )
        db_session.add(telemetry)
        db_session.commit()
        db_session.refresh(telemetry)

        assert telemetry.id is not None
        assert telemetry.humidity is None
        assert telemetry.light is None

    def test_telemetry_relationship_with_zone(self, db_session, sample_zone):
        """Kiểm tra relationship giữa TelemetryData và Zone."""
        telemetry = TelemetryData(
            zone_id=sample_zone.id,
            temperature=30.0,
            measured_at=datetime.now(timezone.utc),
        )
        db_session.add(telemetry)
        db_session.commit()

        assert telemetry.zone is not None
        assert telemetry.zone.name == "Test Zone"


# ── Telemetry History Query Tests ─────────────────────────

class TestTelemetryHistoryQuery:
    """Test cho schema TelemetryHistoryQuery."""

    def test_valid_query_all_fields(self):
        """Tạo query hợp lệ với tất cả các trường."""
        query = TelemetryHistoryQuery(
            zone_id=1,
            metric="temperature",
            date_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
            date_to=datetime(2025, 1, 31, tzinfo=timezone.utc),
            interval="1h",
            limit=500,
        )
        assert query.zone_id == 1
        assert query.metric == "temperature"
        assert query.interval == "1h"
        assert query.limit == 500

    def test_query_with_optional_fields(self):
        """Tạo query chỉ với trường bắt buộc."""
        query = TelemetryHistoryQuery(
            date_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
            date_to=datetime(2025, 1, 31, tzinfo=timezone.utc),
        )
        assert query.zone_id is None
        assert query.metric is None
        assert query.interval == "1m"  # default
        assert query.limit == 1000  # default

    def test_query_invalid_metric(self):
        """Tạo query với metric không hợp lệ."""
        with pytest.raises(Exception):
            TelemetryHistoryQuery(
                metric="invalid_metric",
                date_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
                date_to=datetime(2025, 1, 31, tzinfo=timezone.utc),
            )


# ── Analytics Tests ───────────────────────────────────────

class TestTelemetryAnalytics:
    """Test cho analytics logic."""

    def test_calculate_min_max_avg(self, db_session, sample_zone):
        """Kiểm tra tính toán min/max/avg."""
        now = datetime.now(timezone.utc)
        values = [20.0, 25.0, 30.0, 35.0, 40.0]

        for v in values:
            telemetry = TelemetryData(
                zone_id=sample_zone.id,
                temperature=v,
                measured_at=now,
            )
            db_session.add(telemetry)
        db_session.commit()

        rows = db_session.query(TelemetryData).filter(
            TelemetryData.zone_id == sample_zone.id
        ).all()

        temps = [r.temperature for r in rows if r.temperature is not None]
        assert min(temps) == 20.0
        assert max(temps) == 40.0
        assert round(sum(temps) / len(temps), 2) == 30.0
        assert len(temps) == 5