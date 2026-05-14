"""
Tests cho Report Service.
Chạy: cd backend && python -m pytest tests/test_report_service.py -v
"""
import pytest
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from models import Report, TelemetryData, Zone, User


# ── Test fixtures ──────────────────────────────────────────

@pytest.fixture(scope="module")
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

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
    _, SessionLocal, _ = test_db
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_zone(db_session):
    zone = Zone(name="Report Test Zone", description="For report testing")
    db_session.add(zone)
    db_session.commit()
    db_session.refresh(zone)
    return zone


@pytest.fixture
def sample_telemetry(db_session, sample_zone):
    """Tạo 10 bản ghi telemetry cho zone."""
    import random
    for i in range(10):
        t = TelemetryData(
            zone_id=sample_zone.id,
            temperature=20.0 + random.uniform(-5, 5),
            humidity=50.0 + random.uniform(-10, 10),
            light=300.0 + random.uniform(-50, 50),
            measured_at=datetime.now(timezone.utc),
        )
        db_session.add(t)
    db_session.commit()


# ── Report Model Tests ────────────────────────────────────

class TestReportModel:
    """Test cho Report model."""

    def test_create_report(self, db_session):
        """Tạo report thành công."""
        report = Report(
            name="Test Report",
            report_type="custom",
            format="csv",
            date_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
            date_to=datetime(2025, 1, 31, tzinfo=timezone.utc),
            zone_ids=[1, 2],
            metrics=["temperature", "humidity"],
            status="pending",
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)

        assert report.id is not None
        assert report.name == "Test Report"
        assert report.format == "csv"
        assert report.status == "pending"
        assert report.zone_ids == [1, 2]
        assert report.metrics == ["temperature", "humidity"]

    def test_report_default_status(self, db_session):
        """Trạng thái mặc định là 'pending'."""
        report = Report(
            name="Auto Status Report",
            format="xlsx",
            date_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
            date_to=datetime(2025, 1, 31, tzinfo=timezone.utc),
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)

        assert report.status == "pending"

    def test_report_nullable_zone_ids(self, db_session):
        """zone_ids có thể là None (tất cả khu vực)."""
        report = Report(
            name="All Zones Report",
            format="csv",
            date_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
            date_to=datetime(2025, 1, 31, tzinfo=timezone.utc),
            zone_ids=None,
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)

        assert report.zone_ids is None


# ── Report Generation Tests ───────────────────────────────

class TestReportGeneration:
    """Test cho logic tạo báo cáo."""

    def test_csv_generation_logic(self, db_session, sample_zone, sample_telemetry):
        """Kiểm tra logic tạo CSV từ dữ liệu."""
        import csv
        import io

        rows = db_session.query(
            TelemetryData.zone_id,
            Zone.name.label("zone_name"),
            TelemetryData.temperature,
            TelemetryData.humidity,
            TelemetryData.light,
            TelemetryData.measured_at,
        ).join(Zone, TelemetryData.zone_id == Zone.id).filter(
            TelemetryData.zone_id == sample_zone.id
        ).order_by(TelemetryData.measured_at.asc()).all()

        assert len(rows) == 10
        columns = ["zone_id", "zone_name", "temperature", "humidity", "light", "measured_at"]

        # Tạo CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "zone_id": row.zone_id,
                "zone_name": row.zone_name,
                "temperature": row.temperature,
                "humidity": row.humidity,
                "light": row.light,
                "measured_at": row.measured_at.isoformat() if row.measured_at else None,
            })

        csv_content = output.getvalue()
        assert len(csv_content) > 0
        assert "zone_id" in csv_content
        lines = csv_content.strip().split("\n")
        assert len(lines) == 11  # 1 header + 10 data rows

    def test_empty_data_handling(self, db_session, sample_zone):
        """Xử lý khi không có dữ liệu."""
        rows = db_session.query(
            TelemetryData.zone_id,
            Zone.name.label("zone_name"),
            TelemetryData.temperature,
            TelemetryData.humidity,
            TelemetryData.light,
            TelemetryData.measured_at,
        ).join(Zone, TelemetryData.zone_id == Zone.id).filter(
            TelemetryData.zone_id == 9999  # Zone không tồn tại
        ).all()

        assert len(rows) == 0

    def test_report_file_creation(self, db_session, tmp_path):
        """Kiểm tra tạo file report."""
        import csv
        import io

        # Tạo report record
        report = Report(
            name="File Test Report",
            format="csv",
            date_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
            date_to=datetime(2025, 1, 31, tzinfo=timezone.utc),
            status="processing",
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)

        # Giả lập tạo file
        test_data = [
            {"zone_id": 1, "zone_name": "Zone A", "temperature": 25.0, "humidity": 60.0, "light": 500.0, "measured_at": "2025-01-01T00:00:00"},
            {"zone_id": 1, "zone_name": "Zone A", "temperature": 26.0, "humidity": 62.0, "light": 510.0, "measured_at": "2025-01-01T01:00:00"},
        ]
        columns = ["zone_id", "zone_name", "temperature", "humidity", "light", "measured_at"]

        filename = f"report_{report.id}_test.csv"
        file_path = tmp_path / filename

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(test_data)

        file_path.write_bytes(output.getvalue().encode("utf-8"))

        assert file_path.exists()
        assert file_path.stat().st_size > 0

        # Đọc lại và kiểm tra
        content = file_path.read_text()
        assert "zone_id" in content
        assert len(content.strip().split("\n")) == 3