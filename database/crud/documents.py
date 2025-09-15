# db_utils.py
from sqlalchemy.orm import Session
from sqlalchemy import text

def get_all_company_names(session: Session):
    rows = session.execute(text("SELECT DISTINCT company_name FROM clients_requests ORDER BY company_name ASC")).fetchall()
    return [r[0] for r in rows]

def get_profiles_list(session: Session):
    rows = session.execute(text("SELECT name FROM profiles ORDER BY name ASC")).fetchall()
    return [r[0] for r in rows]

def get_profile_id_by_name(session: Session, profile_name: str):
    return session.execute(text("SELECT id FROM profiles WHERE name = :n"), {"n": profile_name}).scalar()

def get_requests_by_company_and_profile(session: Session, company_name: str, profile_id: int, limit: int = 20):
    rows = session.execute(
        text("""
            SELECT id, created_at
            FROM clients_requests
            WHERE company_name = :company_name AND profile_id = :profile_id
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        {"company_name": company_name, "profile_id": profile_id, "limit": limit}
    ).mappings().all()
    # rows es una lista de dict-like rows con keys: id, created_at
    return rows

def get_required_document_types(session: Session, profile_id: int):
    rows = session.execute(
        text("""
            SELECT id, name, is_required
            FROM document_types
            WHERE profile_id = :pid
            ORDER BY name ASC
        """),
        {"pid": profile_id}
    ).mappings().all()
    return rows

def get_uploaded_documents_map(session: Session, request_id: int):
    rows = session.execute(
        text("""
            SELECT id, document_type_id, file_name, drive_link, uploaded_at, uploaded_by
            FROM uploaded_documents
            WHERE request_id = :rid
        """),
        {"rid": request_id}
    ).mappings().all()
    return {r["document_type_id"]: r for r in rows}

def upsert_uploaded_document(session: Session, request_id: int, document_type_id: int, file_name: str, drive_link: str, uploaded_by: str):
    session.execute(
        text("""
            INSERT INTO uploaded_documents (request_id, document_type_id, file_name, drive_link, uploaded_by)
            VALUES (:request_id, :document_type_id, :file_name, :drive_link, :uploaded_by)
            ON CONFLICT (request_id, document_type_id)
            DO UPDATE SET
                file_name = EXCLUDED.file_name,
                drive_link = EXCLUDED.drive_link,
                uploaded_at = CURRENT_TIMESTAMP,
                uploaded_by = EXCLUDED.uploaded_by
        """),
        {
            "request_id": request_id,
            "document_type_id": document_type_id,
            "file_name": file_name,
            "drive_link": drive_link,
            "uploaded_by": uploaded_by
        }
    )

def get_request_meta(session, request_id: int):
    """
    Devuelve {'notification_followup': str|None, 'general_comments': str|None}
    para la solicitud dada. {} si no existe.
    """
    row = session.execute(
        text("""
            SELECT notification_followup, general_comments
            FROM clients_requests
            WHERE id = :rid
        """),
        {"rid": request_id}
    ).one_or_none()

    if not row:
        return {}
    # row = (notification_followup, general_comments)
    return {
        "notification_followup": row[0],
        "general_comments": row[1],
    }

def update_request_meta(session, request_id: int, notification_followup: str = None, general_comments: str = None):

    session.execute(
        text("""
            UPDATE clients_requests
            SET notification_followup = :nf,
                general_comments      = :gc
            WHERE id = :rid
        """),
        {"nf": notification_followup, "gc": general_comments, "rid": request_id}
    )

def get_first_upload_at(session, request_id: int):
    row = session.execute(
        text("SELECT first_upload_at FROM clients_requests WHERE id = :rid"),
        {"rid": request_id}
    ).one_or_none()
    return row[0] if row else None

def set_first_upload_at_if_null(session, request_id: int, dt):
    session.execute(
        text("""
            UPDATE clients_requests
            SET first_upload_at = COALESCE(first_upload_at, :dt)
            WHERE id = :rid
        """),
        {"rid": request_id, "dt": dt}
    )

def get_requests_for_progress(session, only_for_email: str | None = None):

    sql = text("""
        SELECT
            id,
            company_name,
            profile_id,
            created_at,
            created_by_email
        FROM clients_requests
        WHERE (:email IS NULL OR LOWER(created_by_email) = LOWER(:email))
        ORDER BY created_at DESC
    """)
    rows = session.execute(sql, {"email": only_for_email}).fetchall()
    return [
        {
            "id": r.id,
            "company_name": r.company_name,
            "profile_id": r.profile_id,
            "created_at": r.created_at,
            "created_by_email": r.created_by_email,
        }
        for r in rows
    ]