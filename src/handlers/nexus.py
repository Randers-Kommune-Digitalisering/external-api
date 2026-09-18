import logging

from datetime import datetime

from extensions import db
from models.nexus import PersonligtHjaelpemiddel, Staastoettestol

logger = logging.getLogger(__name__)


def _prepare_common_form_data(data: dict) -> dict:
    cpr = data["cpr"]
    form_date = datetime.fromisoformat(data["date"].replace("Z", "+00:00")).date()
    form_pdf_base64 = data["formData"]
    attachments = data["attachments"]
    can_collect_data: bool = data.get("canCollectData", False) is True
    for_another = data.get("forAnother", False)

    if for_another:
        relation = data.get("relation") or ""
        on_behalf_of_relation = "Pårørende" if any(value in relation.lower() for value in ("forælder", "barn")) else "Andre" if "anden relation" in relation.lower() else None
        on_behalf_of_name = data["text1"] if data["text1"] else None
        on_behalf_of_phone = data["text2"] if data["text2"] else None
        on_behalf_of_text = f"Borger er {relation.lower()}" if on_behalf_of_relation != "Andre" else f"{relation} - {data.get('text3')}"
    else:
        on_behalf_of_relation = None
        on_behalf_of_name = None
        on_behalf_of_phone = None
        on_behalf_of_text = None

    return {
        "cpr": cpr,
        "form_date": form_date,
        "form_pdf_base64": form_pdf_base64,
        "attachments": attachments,
        "can_collect_data": can_collect_data,
        "for_another": for_another,
        "on_behalf_of_relation": on_behalf_of_relation,
        "on_behalf_of_name": on_behalf_of_name,
        "on_behalf_of_phone": on_behalf_of_phone,
        "on_behalf_of_text": on_behalf_of_text,
    }


def personligt_hjaelpemiddel(data: dict) -> bool:
    try:
        common_form_data = _prepare_common_form_data(data)

        device_name = data["text0"]

        form_doc_name = (
            f"Ansøgning {device_name}"
            if (device_name or "").replace(" ", "").strip()
            else "Ansøgning Personlig hjælpemiddel"
        )
        attachment_doc_name = f"Ansøgning Bilag {device_name}" if (device_name or "").replace(" ", "").strip() else "Ansøgning Bilag Personlig hjælpemiddel"

        renewal_or_new_text = data.get("text4")
        formatted_form_date = common_form_data["form_date"].strftime("%d-%m-%Y")
        reason_text = f"{formatted_form_date} - Digital ansøgning om {device_name}" if (device_name or "").replace(" ", "").strip() else f"{formatted_form_date} - Ansøgning om Personlig hjælpemiddel"
        if len(common_form_data["attachments"]) > 1:
            reason_text += " med bilag"
        reason_text += f" {renewal_or_new_text}"

        personligt_hjaelpemiddel = PersonligtHjaelpemiddel(
            form_doc_name=form_doc_name,
            attachment_doc_name=attachment_doc_name,
            device_name=device_name,
            reason_text=reason_text,
            renewal_or_new_text=renewal_or_new_text or "",
            **common_form_data,
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


def staastoettestol(data: dict) -> bool:
    try:
        common_form_data = _prepare_common_form_data(data)

        device_name = data["text0"] if (data["text0"] or "").replace(" ", "").strip() else "Ståstøttestol"

        form_doc_name = f"Ansøgning {device_name}"
        attachment_doc_name = f"Ansøgning Bilag {device_name}" if (device_name or "").replace(" ", "").strip() else "Ansøgning Bilag Personlig hjælpemiddel"

        renewal_or_new_text = data.get("text4")
        reason_text = data.get("text5")

        staastoettestol = Staastoettestol(
            form_doc_name=form_doc_name,
            attachment_doc_name=attachment_doc_name,
            device_name=device_name,
            reason_text=reason_text,
            renewal_or_new_text=renewal_or_new_text or "",
            **common_form_data,
        )
    except Exception:
        logger.exception("Failed to prepare standing support chair form")
        return False

    try:
        db.session.add(staastoettestol)
        db.session.commit()
    except Exception:
        logger.exception("Failed to save standing support chair form")
        db.session.rollback()
        return False
    return True


HJAELPEMIDDEL_HANDLERS = {
    "personligt_hjaelpemiddel": personligt_hjaelpemiddel,
    "staastoettestol": staastoettestol,
    "personligt_hjaelpemiddel__kopi__test": personligt_hjaelpemiddel,  # Test form for testing purposes, should be removed in production
    "staastoettestol__kopi__test": staastoettestol,  # Test form for testing purposes, should be removed in production
}
