"""
Shared test fixtures cho SmartFarm backend.
Sử dụng SQLite in-memory với transaction rollback để test độc lập.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from database import Base


@pytest.fixture(scope="session")
def engine():
    """Tạo engine một lần cho toàn bộ test session."""
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=_engine)
    yield _engine
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture(scope="function")
def db(engine):
    """Tạo session mới cho mỗi test function với transaction rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)

    yield session

    session.remove()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_zone(db):
    """Tạo zone mẫu."""
    from models import Zone
    # Xóa hết dữ liệu cũ trong bảng zones trước khi tạo
    db.query(Zone).delete()
    db.commit()
    zone = Zone(name="Test Zone", description="Zone for testing")
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@pytest.fixture
def sample_user(db):
    """Tạo user mẫu."""
    from models import User
    from auth import get_password_hash
    user = User(
        username="testuser",
        hashed_password=get_password_hash("testpass123"),
        name="Test User",
        role="ADMIN"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_telemetry(db, sample_zone):
    """Tạo 5 bản ghi telemetry cho zone."""
    from models import TelemetryData
    from datetime import datetime, timezone
    import random

    for i in range(5):
        t = TelemetryData(
            zone_id=sample_zone.id,
            temperature=20.0 + random.uniform(-5, 5),
            humidity=50.0 + random.uniform(-10, 10),
            light=300.0 + random.uniform(-50, 50),
            measured_at=datetime.now(timezone.utc),
        )
        db.add(t)
    db.commit()