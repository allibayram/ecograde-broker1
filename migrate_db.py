import sqlite3

def add_column():
    try:
        conn = sqlite3.connect('broker.db')
        c = conn.cursor()
        c.execute("ALTER TABLE guaranteed_lots ADD COLUMN quality_score_numeric FLOAT")
        conn.commit()
        conn.close()
        print("Column added successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_column()
