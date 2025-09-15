# views/visualization.py

import streamlit as st
import unicodedata
from database.db import SessionLocal
from database.crud.documents import (
    get_profiles_list,           # <- lista de NOMBRES de perfil
    get_profile_id_by_name,      # <- resuelve ID a partir del nombre
    get_required_document_types,
    get_uploaded_documents_map,
    get_request_meta,
    get_requests_for_progress,   # <- devuelve todas o por email del creador
)

# --------------------
# Helpers
# --------------------
def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s.strip().lower()

def is_security_verification(doc_name: str) -> bool:
    # Solo este documento admite múltiples archivos (CSV en file_name/drive_link)
    return "verificaciones de seguridad" in _slug(doc_name)

def split_csv_list(s: str):
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x and x.strip()]

# --------------------
# Main
# --------------------
def show(current_user_email: str | None = None, is_admin: bool = False):
    """
    - Admin: ve todas las solicitudes.
    - No admin: solo las que creó (created_by_email == current_user_email).
    Luego se filtra por compañía/perfil dentro del conjunto permitido.
    """
    st.subheader("📊 Progreso de carga de documentos")

    session = SessionLocal()
    try:
        # 1) Traer solicitudes según rol
        email_filter = None if is_admin else (current_user_email or None)
        requests = get_requests_for_progress(session, only_for_email=email_filter)
        if not requests:
            st.info("No hay solicitudes para mostrar.")
            return

        # 2) Construir listas a partir del conjunto filtrado
        companies = sorted({r.get("company_name") for r in requests if r.get("company_name")})

        # Mapa nombre->id para TODOS los perfiles definidos en el sistema
        all_profile_names = get_profiles_list(session) or []  # p.ej. ["Cliente", "Proveedor", ...]
        name_to_id = {}
        for name in all_profile_names:
            pid = get_profile_id_by_name(session, name)
            if pid:
                name_to_id[name] = pid

        # Perfiles realmente presentes en las solicitudes filtradas (disponibles para selección)
        present_profile_ids = {r.get("profile_id") for r in requests if r.get("profile_id") is not None}
        available_profiles = [(name, pid) for name, pid in name_to_id.items() if pid in present_profile_ids]
        # Orden alfabético por nombre
        available_profiles.sort(key=lambda x: x[0])

        col1, col2 = st.columns(2)
        with col1:
            company_name = st.selectbox(
                "Nombre de la compañía",
                companies,
                index=None,
                placeholder="Selecciona la compañía...",
                key="pv_company_selector"
            )
        with col2:
            profile_name = st.selectbox(
                "Perfil 1234",
                [name for (name, _) in available_profiles],
                index=None,
                placeholder="Selecciona el perfil...",
                key="pv_profile_selector"
            )

        if not company_name or not profile_name:
            st.info("Selecciona compañía y perfil para continuar.")
            return

        # Resolver profile_id a partir del nombre elegido
        profile_id = name_to_id.get(profile_name)
        if not profile_id:
            st.error("❌ El perfil seleccionado no existe en la base de datos.")
            return

        # 3) Filtrar las solicitudes (dentro del conjunto permitido) por compañía y perfil
        filtered_requests = [
            r for r in requests
            if r.get("company_name") == company_name and r.get("profile_id") == profile_id
        ]
        if not filtered_requests:
            st.warning("No hay solicitudes para esta compañía y perfil (con los permisos actuales).")
            return

        # 4) Elegir solicitud si hay varias
        options = [
            f"ID {r['id']} • {r['created_at'].strftime('%Y-%m-%d %H:%M')} • {r.get('created_by_email') or ''}"
            for r in filtered_requests
        ]
        idx = 0
        if len(options) > 1:
            idx = st.selectbox(
                "Selecciona la solicitud",
                list(range(len(options))),
                index=None,
                placeholder="Selecciona una solicitud...",
                format_func=lambda i: options[i],
                key="pv_request_selector"
            )
            if idx is None:
                st.info("Selecciona una solicitud para continuar.")
                return

        selected_request = filtered_requests[idx]
        request_id = selected_request["id"]

        # 5) Cálculo de progreso (ANTES de listar documentos)
        required_docs = get_required_document_types(session, profile_id)  # [{id, name, is_required}, ...]
        uploaded_map  = get_uploaded_documents_map(session, request_id)   # {document_type_id: {...}}

        if not required_docs:
            st.info("Este perfil no tiene tipos de documentos configurados.")
            return

        total_required = sum(1 for d in required_docs if d.get("is_required"))

        uploaded_required = 0
        for d in required_docs:
            if not d.get("is_required"):
                continue
            rec = uploaded_map.get(d["id"])
            if not rec:
                continue
            if is_security_verification(d["name"]):
                urls = split_csv_list(rec.get("drive_link") or "")
                if urls:
                    uploaded_required += 1
            else:
                if (rec.get("drive_link") or "").strip():
                    uploaded_required += 1

        completion = int(round((uploaded_required / total_required) * 100)) if total_required else 100

        colA, colB = st.columns([1, 3])
        with colA:
            st.metric("Completitud", f"{completion}%")
            st.caption(f"{uploaded_required}/{total_required} requeridos cargados" if total_required else "Sin documentos requeridos")
        with colB:
            st.text("")
            st.text("")
            st.text("")
            st.progress(completion / 100)

        # 6) Detalle de documentos
        st.write("---")
        st.caption("Estado de documentos.")

        for doc in required_docs:
            doc_id = doc["id"]
            doc_name = doc["name"]
            is_required = bool(doc.get("is_required"))
            row = uploaded_map.get(doc_id)

            if is_security_verification(doc_name):
                # Múltiples enlaces separados por comas
                links_csv = row.get("drive_link") if row else ""
                names_csv = row.get("file_name") if row else ""
                urls = split_csv_list(links_csv)
                names = split_csv_list(names_csv)

                if urls:
                    st.markdown(f"✅ **{doc_name}**{' (obligatorio)' if is_required else ''} — {len(urls)} archivo(s):")
                    for i, u in enumerate(urls):
                        label = names[i] if i < len(names) else f"Archivo {i+1}"
                        st.markdown(f"- [{label}]({u})")
                else:
                    st.markdown(f"❌ **{doc_name}**{' (obligatorio)' if is_required else ''} — No cargado")
            else:
                link = row.get("drive_link") if row else None
                if (link or "").strip():
                    st.markdown(f"✅ **{doc_name}**{' (obligatorio)' if is_required else ''} — [Ver archivo]({link})")
                else:
                    st.markdown(f"❌ **{doc_name}**{' (obligatorio)' if is_required else ''} — No cargado")

        # 7) Seguimiento y comentarios (solo si hay info)
        meta = get_request_meta(session, request_id) or {}
        notif = (meta.get("notification_followup") or "").strip()
        comms = (meta.get("general_comments") or "").strip()

        if notif or comms:
            st.write("---")
            st.markdown("**Seguimiento y comentarios**")

            if notif and comms:
                colN, colC = st.columns(2)
                with colN:
                    with st.expander("Ver seguimiento", expanded=True):
                        st.markdown(notif)
                with colC:
                    with st.expander("Ver comentarios", expanded=True):
                        st.markdown(comms)
            elif notif:
                st.markdown("**Seguimiento de notificación**")
                with st.expander("Ver seguimiento", expanded=True):
                    st.markdown(notif)
            else:
                st.markdown("**Comentarios generales**")
                with st.expander("Ver comentarios", expanded=True):
                    st.markdown(comms)

    finally:
        session.close()
