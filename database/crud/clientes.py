import psycopg2
import os

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        dbname=os.getenv("DB_NAME", "compliance_db"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "admin"),
        port=os.getenv("DB_PORT", 5432)
    )

def get_profile_id(profile_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM profiles WHERE name = %s", (profile_name.lower(),))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

def insert_client_request(profile_id, company_name=None, email=None, trading=None, location=None, language=None, reminder_frequency=None,
                            colaborador_nombre=None,colaborador_cedula=None, requested_by: str = None,  requested_by_type: str = None):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO clients_requests (
            profile_id, company_name, email, trading, location, language, reminder_frequency, colaborador_nombre, colaborador_cedula, requested_by, requested_by_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (
        profile_id, company_name, email, trading, location, language, reminder_frequency, colaborador_nombre, colaborador_cedula, requested_by, requested_by_type))

    request_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return request_id

