import os
from sqlalchemy import text
from database import engine

def run_migration():
    with engine.begin() as conn:
        print("Starting Database Migration (Phase 8)...")
        
        try:
            conn.execute(text("ALTER TABLE offers ADD COLUMN custom_fields JSON;"))
        except: pass
            
        try:
            conn.execute(text("ALTER TABLE guaranteed_lots ADD COLUMN custom_fields JSON;"))
        except: pass
        
        # Cleanup
        tables = ["messages", "conversations", "orders", "guaranteed_lots", "offers"]
        for t in tables:
            try:
                conn.execute(text(f"DELETE FROM {t};"))
            except: pass
        
        print("🧹 Cleaned up ALL old test records! Migration complete.")

if __name__ == "__main__":
    run_migration()
