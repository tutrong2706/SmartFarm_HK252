"""Migration: Add widgets column to reports table."""
from sqlalchemy import text
from database import engine

def add_widgets_column():
    """Add widgets JSON column to reports table if it doesn't exist."""
    with engine.connect() as connection:
        # Check if column exists
        result = connection.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='reports' AND column_name='widgets'
        """))
        
        if not result.fetchone():
            # Add widgets column
            connection.execute(text("""
                ALTER TABLE reports ADD COLUMN widgets JSON
            """))
            connection.commit()
            print("✅ Added 'widgets' column to 'reports' table successfully!")
        else:
            print("✓ 'widgets' column already exists in 'reports' table")

if __name__ == "__main__":
    add_widgets_column()
