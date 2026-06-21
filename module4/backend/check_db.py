import psycopg2

conn = psycopg2.connect("postgresql://postgres:Vortexa0322315@db.ccukhfuptshsbmhalqxy.supabase.co:5432/postgres")
cur = conn.cursor()

def check_table(table):
    try:
        cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'id';")
        print(f"Table {table} id column type:", cur.fetchall())
        cur.execute(f"SELECT id FROM {table} LIMIT 1;")
        print(f"Sample id from {table}:", cur.fetchone())
    except Exception as e:
        print(f"Error checking {table}:", e)
        conn.rollback()

check_table('doctors')
check_table('patient_records')

