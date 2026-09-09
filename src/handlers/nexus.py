import logging

from datetime import datetime

from extensions import db
from models.nexus import PersonligtHjaelpemiddel

logger = logging.getLogger(__name__)


def personligt_hjaelpemiddel(data: dict) -> bool:
    try:
        cpr = data["cpr"]
        form_date = datetime.fromisoformat(data["date"].replace("Z", "+00:00")).date()

        device_name = data["text0"]

        form_doc_name = f"Ansøgning {device_name}" if device_name.replace(" ", "").strip() else "Ansøgning Personlig hjælpemiddel"
        form_pdf_base64 = data["formData"]
        attachment_doc_name = f"Ansøgning Bilag {device_name}" if device_name.replace(" ", "").strip() else "Ansøgning Bilag Personlig hjælpemiddel"
        attachments = data["attachments"]

        can_collect_data: bool = data.get("canCollectData", False) is True

        for_another = data.get("forAnother", False)

        if for_another:
            on_behalf_of_relation = "Pårørende" if any(value in (data.get("relation") or "").lower() for value in ("forælder", "barn")) else "Andre" if "anden relation" in (data.get("relation") or "").lower() else None
            on_behalf_of_name = data["text1"] if data["text1"] else None
            on_behalf_of_phone = data["text2"] if data["text2"] else None
            on_behalf_of_text = f"Borger er {(data.get('relation') or '').lower()}" if on_behalf_of_relation != "Andre" else f"{data.get('relation')} - {data.get('text3')}"
        else:
            on_behalf_of_relation = None
            on_behalf_of_name = None
            on_behalf_of_phone = None
            on_behalf_of_text = None

        renewal_or_new_text = data.get("text4")
        formatted_form_date = form_date.strftime("%d-%m-%Y")
        reason_text = f"{formatted_form_date} - Digital ansøgning om {device_name}" if device_name.replace(" ", "").strip() else f"{formatted_form_date} - Ansøgning om Personlig hjælpemiddel"
        if len(attachments) > 1:
            reason_text += " med bilag"
        reason_text += f" {renewal_or_new_text}"

        personligt_hjaelpemiddel = PersonligtHjaelpemiddel(
            cpr=cpr,
            form_date=form_date,
            form_doc_name=form_doc_name,
            form_pdf_base64=form_pdf_base64,
            attachment_doc_name=attachment_doc_name,
            attachments=attachments,
            device_name=device_name,
            can_collect_data=can_collect_data,
            for_another=for_another,
            reason_text=reason_text,
            renewal_or_new_text=renewal_or_new_text or "",
            on_behalf_of_relation=on_behalf_of_relation,
            on_behalf_of_name=on_behalf_of_name,
            on_behalf_of_phone=on_behalf_of_phone,
            on_behalf_of_text=on_behalf_of_text,
        )
    except Exception:
        logger.exception("Failed to prepare personal assistive-device form")
        return False

    try:
        db.session.add(personligt_hjaelpemiddel)
        db.session.commit()
    except Exception:
        logger.exception("Failed to save personal assistive-device form")
        db.session.rollback()
        return False
    return True


HJAELPEMIDDEL_HANDLERS = {
    "personligt_hjaelpemiddel": personligt_hjaelpemiddel,
    "personligt_hjaelpemiddel__kopi__test": personligt_hjaelpemiddel  # Test form for testing purposes, should be removed in production
}
