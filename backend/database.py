from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Thay đổi thông tin kết nối này theo PostgreSQL của bạn
# Format: postgresql://<username>:<password>@<host>:<port>/<database_name>
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:27062005@localhost:5432/smart_farm_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency để sử dụng trong các API (Dependency Injection)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()