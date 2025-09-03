# progress_view.py

import unicodedata
import streamlit as st
from database.db import SessionLocal
from database.crud.documents import (
    get_all_company_names,
    get_profiles_list,
    get_profile_id_by_name,
    get_requests_by_company_and_profile,
    get_required_document_types,
    get_uploaded_documents_map,
    get_request_meta,
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

def progress_view():
    st.subheader("📊 Progreso de carga de documentos")

    session = SessionLocal()
    try:
        companies = get_all_company_names(session) or []
        profiles  = get_profiles_list(session) or []

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
                "Perfil",
                profiles,
                index=None,
                placeholder="Selecciona el perfil...",
                key="pv_profile_selector"
            )

        if not company_name or not profile_name:
            st.info("Selecciona compañía y perfil para continuar.")
            return

        profile_id = get_profile_id_by_name(session, profile_name)
        if not profile_id:
            st.error("❌ El perfil seleccionado no existe en la base de datos.")
            return

        # Solicitudes de esa compañía + perfil
        requests = get_requests_by_company_and_profile(session, company_name, profile_id)
        if not requests:
            st.warning("No hay solicitudes para esta compañía y perfil.")
            return

        # Elegir solicitud si hay varias
        options = [f"ID {r['id']} • {r['created_at'].strftime('%Y-%m-%d %H:%M')}" for r in requests]
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
            selected_request = requests[idx]
        else:
            selected_request = requests[0]

        request_id = selected_request["id"]

        # ---- Cálculo de progreso (ANTES de listar documentos) ----
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
                if rec.get("drive_link"):
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

        # ---- Detalle de documentos ----
        st.write("---")
        st.caption("Estado de documentos.")

        missing_required = []
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
                    if is_required:
                        missing_required.append(doc_name)
            else:
                link = row.get("drive_link") if row else None
                if link:
                    st.markdown(f"✅ **{doc_name}**{' (obligatorio)' if is_required else ''} — [Ver archivo]({link})")
                else:
                    st.markdown(f"❌ **{doc_name}**{' (obligatorio)' if is_required else ''} — No cargado")
                    if is_required:
                        missing_required.append(doc_name)

        # ---- Seguimiento y comentarios (solo si hay info) ----
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
