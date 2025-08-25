# form_documents_existing.py

import os
import streamlit as st
from datetime import datetime
from database.db import SessionLocal
from database.crud.documents import (
    get_all_company_names,
    get_profiles_list,
    get_profile_id_by_name,
    get_requests_by_company_and_profile,
    get_required_document_types,
    get_uploaded_documents_map,
    upsert_uploaded_document,
    get_request_meta,  
    update_request_meta,
)
from services.google_drive_utils import init_drive, find_or_create_folder, upload_to_drive

def forms():
    st.subheader("📎 Carga de documentos")

    session = SessionLocal()

    try:
        # 1) Selectboxes para buscar la solicitud
        companies = get_all_company_names(session)
        profiles = get_profiles_list(session)

        col1, col2 = st.columns(2)
        with col1:
            company_name = st.selectbox(
                "Nombre de la compañía",
                companies,
                index=None if companies else None,
                placeholder="Selecciona la compañía...",
                key="company_selector"
            )
        with col2:
            profile_name = st.selectbox(
                "Perfil",
                profiles,
                index=None if profiles else None,
                placeholder="Selecciona el perfil...",
                key="profile_selector"
            )

        if not company_name or not profile_name:
            st.info("Selecciona una compañía y un perfil para continuar.")
            return

        profile_id = get_profile_id_by_name(session, profile_name)
        if not profile_id:
            st.error("❌ El perfil seleccionado no existe en la base de datos.")
            return

        # 2) Buscar solicitudes existentes por compañía + perfil
        requests = get_requests_by_company_and_profile(session, company_name, profile_id)
        if not requests:
            st.warning("No hay solicitudes para esta compañía y perfil. Crea primero una solicitud en el formulario de registro.")
            return

        options = [f"ID {r['id']} • {r['created_at'].strftime('%Y-%m-%d %H:%M')}" for r in requests]
        idx = 0
        if len(options) > 1:
            idx = st.selectbox(
                "Selecciona la solicitud",
                list(range(len(options))),
                format_func=lambda i: options[i],
                index=None,
                placeholder="Selecciona una solicitud..."
            )
            if idx is None:
                st.info("Selecciona una solicitud para continuar.")
                return

        selected_request = requests[idx if len(options) > 1 else 0]
        request_id = selected_request["id"]

        # 3) Documentos requeridos del perfil + ya subidos para esta solicitud
        required_docs = get_required_document_types(session, profile_id)  # [{id, name, is_required}, ...]
        uploaded_map = get_uploaded_documents_map(session, request_id)    # {doc_type_id: row}

        st.caption("Sube los documentos. Los ya subidos muestran enlace.")
        uploaded_buffers = {}
        pending_count = 0

        for doc in required_docs:
            doc_id = doc["id"]
            doc_name = doc["name"]
            already = uploaded_map.get(doc_id)
            link = already.get("drive_link") if already else None

            if link:
                st.markdown(f"✅ **{doc_name}** — [Ver archivo]({link})")
                continue

            req_mark = " (obligatorio)" if doc.get("is_required") else ""
            st.markdown(f"❌ **{doc_name}**{req_mark} — No cargado")

            uploaded_buffers[doc_id] = st.file_uploader(
                label=f"📁 Subir {doc_name}",
                type=["pdf"],
                key=f"uploader_{request_id}_{doc_id}"
            )
            st.write("")  # espaciado
            pending_count += 1

        # --- Seguimiento y comentarios forman parte del mismo guardado ---
        st.markdown("---")
        st.subheader("🧭 Seguimiento y comentarios")

        meta = get_request_meta(session, request_id) or {}
        notif_default = meta.get("notification_followup") or ""
        comments_default = meta.get("general_comments") or ""

        seguimiento_text = st.text_area(
            "Seguimiento de notificación",
            value=notif_default,
            placeholder="Ej.: 2025-08-20: Enviado correo a contacto@empresa.com\n2025-08-22: Responden que adjuntan doc. pendiente...",
            key=f"seguimiento_{request_id}",
            height=150
        )

        comentarios_text = st.text_area(
            "Comentarios generales",
            value=comments_default,
            placeholder="Observaciones generales de la solicitud / riesgos / acuerdos / notas internas.",
            key=f"comentarios_{request_id}",
            height=150
        )

        # Botón ÚNICO: guarda documentos (si hay) y notas SIEMPRE
        label_btn = "Guardar documentos y notas" if pending_count > 0 else "Guardar notas"
        if st.button(label_btn, key=f"btn_guardar_integrado_{request_id}"):
            with st.spinner("Guardando cambios..."):
                try:
                    changes = 0

                    # 1) Subir documentos seleccionados (si hay)
                    any_file_selected = any(uploaded_buffers.get(d["id"]) for d in required_docs)
                    if any_file_selected:
                        service = init_drive()
                        shared_drive_id = st.secrets["drive"].get("shared_drive_id")
                        parent_folder_id = st.secrets["drive"].get("parent_folder_id")

                        folder_name = f"Solicitud - {company_name} - {profile_name}"
                        folder_id = find_or_create_folder(
                            service,
                            folder_name,
                            shared_drive_id=shared_drive_id if not parent_folder_id else None,
                            parent_folder_id=parent_folder_id,
                        )

                        for doc in required_docs:
                            doc_id = doc["id"]
                            file = uploaded_buffers.get(doc_id)
                            if not file:
                                continue

                            tmp_path = f"/tmp/{request_id}_{doc_id}_{file.name}"
                            with open(tmp_path, "wb") as f:
                                f.write(file.getbuffer())

                            drive_link = upload_to_drive(service, folder_id, tmp_path, file.name)

                            upsert_uploaded_document(
                                session=session,
                                request_id=request_id,
                                document_type_id=doc_id,
                                file_name=file.name,
                                drive_link=drive_link,
                                uploaded_by=(getattr(st, "user", None).name if getattr(st, "user", None) else "system")
                            )
                            changes += 1

                            try:
                                os.remove(tmp_path)
                            except Exception:
                                pass

                    # 2) Guardar seguimiento y comentarios SIEMPRE (parte del formulario normal)
                    update_request_meta(session, request_id, seguimiento_text, comentarios_text)

                    # 3) Commit único
                    session.commit()

                    if changes:
                        st.success(f"✅ {changes} documento(s) cargado(s)/actualizado(s) y notas guardadas.")
                    else:
                        st.success("✅ Notas guardadas.")
                except Exception as e:
                    session.rollback()
                    st.error(f"❌ Error al guardar: {e}")

        # Mensaje informativo si no hay pendientes
        if pending_count == 0:
            st.info("No hay documentos pendientes por subir. Puedes actualizar las notas y guardarlas.")
    finally:
        session.close()
