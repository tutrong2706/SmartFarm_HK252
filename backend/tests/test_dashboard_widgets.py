"""
Tests cho Dashboard Widget Service.
Chạy: cd backend && python -m pytest tests/test_dashboard_widgets.py -v
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from models import DashboardWidget, User, Zone


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


class TestDashboardWidgetModel:
    """Test cho DashboardWidget model."""

    def test_create_widget(self, db_session):
        """Tạo widget thành công."""
        widget = DashboardWidget(
            widget_type="stat_card",
            title="Nhiệt độ trung bình",
            config={"metric": "temperature", "zone_id": None, "agg": "avg"},
            position=0,
            is_active=True,
        )
        db_session.add(widget)
        db_session.commit()
        db_session.refresh(widget)

        assert widget.id is not None
        assert widget.widget_type == "stat_card"
        assert widget.title == "Nhiệt độ trung bình"
        assert widget.config == {"metric": "temperature", "zone_id": None, "agg": "avg"}
        assert widget.position == 0
        assert widget.is_active is True

    def test_create_widget_with_user(self, db_session):
        """Tạo widget gắn với user."""
        from auth import get_password_hash
        user = User(
            username="widgetuser",
            hashed_password=get_password_hash("pass123"),
            name="Widget User",
            role="ADMIN"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        widget = DashboardWidget(
            user_id=user.id,
            widget_type="line_chart",
            title="Biểu đồ nhiệt độ",
            config={"metrics": ["temperature"], "zone_ids": [1], "period": "24h"},
            position=1,
        )
        db_session.add(widget)
        db_session.commit()
        db_session.refresh(widget)

        assert widget.user_id == user.id
        assert widget.user is not None
        assert widget.user.username == "widgetuser"

    def test_create_widget_default_values(self, db_session):
        """Kiểm tra giá trị mặc định."""
        widget = DashboardWidget(
            widget_type="gauge",
            title="Đồng hồ đo",
            config={"metric": "humidity", "zone_id": 1, "min": 0, "max": 100},
            position=0,
        )
        db_session.add(widget)
        db_session.commit()
        db_session.refresh(widget)

        assert widget.is_active is True  # default
        assert widget.created_at is not None

    def test_widget_types_enum(self, db_session):
        """Kiểm tra các widget type hợp lệ."""
        valid_types = ["stat_card", "line_chart", "bar_chart", "gauge", "live_table"]
        for i, wtype in enumerate(valid_types):
            widget = DashboardWidget(
                widget_type=wtype,
                title=f"Widget {wtype}",
                config={},
                position=i,
            )
            db_session.add(widget)
        db_session.commit()

        widgets = db_session.query(DashboardWidget).all()
        assert len(widgets) == len(valid_types)


class TestWidgetReorder:
    """Test cho logic sắp xếp lại widgets."""

    def test_reorder_positions(self, db_session):
        """Kiểm tra thay đổi vị trí widget."""
        widgets = []
        for i in range(5):
            w = DashboardWidget(
                widget_type="stat_card",
                title=f"Widget {i}",
                config={},
                position=i,
            )
            db_session.add(w)
            widgets.append(w)
        db_session.commit()

        # Giả lập reorder: [0,1,2,3,4] -> [0,2,1,3,4]
        order = [widgets[0].id, widgets[2].id, widgets[1].id, widgets[3].id, widgets[4].id]
        for position, widget_id in enumerate(order):
            w = db_session.query(DashboardWidget).filter(DashboardWidget.id == widget_id).first()
            w.position = position
        db_session.commit()

        # Kiểm tra lại thứ tự
        all_widgets = db_session.query(DashboardWidget).order_by(DashboardWidget.position.asc()).all()
        assert all_widgets[0].id == widgets[0].id
        assert all_widgets[1].id == widgets[2].id
        assert all_widgets[2].id == widgets[1].id
        assert all_widgets[3].id == widgets[3].id
        assert all_widgets[4].id == widgets[4].id