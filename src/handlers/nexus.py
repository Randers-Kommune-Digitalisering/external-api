import logging

from datetime import datetime

from extensions import db
from models.nexus import (
    PersonligtHjaelpemiddel,
    Staastoettestol,
    Elscooter,
    Servicehund,
    Kommunikationshjaelpemiddel,
    HjaelpemiddelAndreTyperAfHjaelpemidler,
    HjaelpemiddelTilBarn,
    StoetteTilBil,
    SaerligIndretningAfBilKoerekort,
    Boligindretning
)
from utils.utils import danish_to_ascii

logger = logging.getLogger(__name__)


def _normalize_form_name(form_name: str) -> str:
    return danish_to_ascii(form_name.replace(" ", "_").replace("-", "")).lower().removesuffix("__kopi__test")


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
        if len(common_form_data["attachments"]) > 0:
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


def sel_112_113_113b_116(data: dict) -> bool:
    try:
        common_form_data = _prepare_common_form_data(data)
        form_name = _normalize_form_name(data["formName"])
        form_model = {
            "staastoettestol": Staastoettestol,
            "elscooter": Elscooter,
            "servicehund": Servicehund,
            "kommunikationshjaelpemiddel": Kommunikationshjaelpemiddel,
            "hjaelpemiddel_andre_typer_af_hjaelpemidler": HjaelpemiddelAndreTyperAfHjaelpemidler,
            "boligindretning": Boligindretning,
        }.get(form_name)
        if form_model is None:
            raise ValueError(f"Unsupported form name: {form_name}")

        default_device_name = "Elscooter" if form_name == "elscooter" else "Ståstøttestol"
        device_name = data["text0"] if (data["text0"] or "").replace(" ", "").strip() else default_device_name

        form_doc_name = f"Ansøgning {device_name}"
        attachment_doc_name = f"Ansøgning Bilag {device_name}" if (device_name or "").replace(" ", "").strip() else "Ansøgning Bilag Personlig hjælpemiddel"

        renewal_or_new_text = data.get("text4")
        reason_text = data.get("text5")

        form = form_model(
            form_doc_name=form_doc_name,
            attachment_doc_name=attachment_doc_name,
            device_name=device_name,
            reason_text=reason_text,
            renewal_or_new_text=renewal_or_new_text or "",
            **common_form_data,
        )
    except Exception:
        logger.exception(f"Failed to prepare {form_name} form")
        return False

    try:
        db.session.add(form)
        db.session.commit()
    except Exception:
        logger.exception(f"Failed to save {form_name} form")
        db.session.rollback()
        return False
    return True


def sel_114(data: dict) -> bool:
    try:
        common_form_data = _prepare_common_form_data(data)
        form_name = _normalize_form_name(data["formName"])
        form_model = {
            "stoette_til_bil": StoetteTilBil,
            "saerlig_indretning_af_bil_koerekort": SaerligIndretningAfBilKoerekort,
        }.get(form_name)
        if form_model is None:
            raise ValueError(f"Unsupported form name: {form_name}")

        device_name = data.get("text0")

        form_doc_name = f"Ansøgning {device_name}"
        attachment_doc_name = f"Ansøgning Bilag {device_name}" if (device_name or "").replace(" ", "").strip() else "Ansøgning Bilag Personlig hjælpemiddel"

        renewal_or_new_text = data.get("text4")
        reason_text = data.get("text5")
        type1 = (data.get("text6") or "").strip()
        type2 = (data.get("text7") or "").strip()

        if type1 and type2:
            type_text = "§ 114 trivsel"
        elif type1:
            type_text = type1
        elif type2:
            type_text = type2
        else:
            raise ValueError("At least one of type1 or type2 must be provided")

        form = form_model(
            form_doc_name=form_doc_name,
            attachment_doc_name=attachment_doc_name,
            device_name=device_name,
            reason_text=reason_text,
            type_text=type_text,
            renewal_or_new_text=renewal_or_new_text or "",
            **common_form_data,
        )
    except Exception:
        logger.exception(f"Failed to prepare {form_name} form")
        return False

    try:
        db.session.add(form)
        db.session.commit()
    except Exception:
        logger.exception(f"Failed to save {form_name} form")
        db.session.rollback()
        return False
    return True


def hjaelpemiddel_barn(data: dict) -> bool:
    form_name = _normalize_form_name(data["formName"])
    form_model = {
        "hjaelpemiddel_til_barn": HjaelpemiddelTilBarn,
    }.get(form_name)

    if not form_model:
        logger.error(f"Form model for '{form_name}' not found")
        return False

    cpr = data.get("cpr")
    form_date = datetime.fromisoformat(data["date"].replace("Z", "+00:00")).date()
    form_doc_name = f"Ansøgning {data.get('formName')}"
    attachment_doc_name = f"Ansøgning {data.get('formName')} Bilag"
    form_pdf_base64 = data["formData"]
    attachments = data["attachments"]

    for_another = data.get("forAnother", True) or True

    can_collect_data: bool = data.get("canCollectData", False) is True
    device_name = data.get("text0") or "Hjælpemiddel til barn"
    reason_text = data.get("text5") or "Digital ansøgning hjælpemiddel til barn"

    relation = data.get("relation") or ""
    on_behalf_of_relation = "Pårørende" if any(value in relation.lower() for value in ("forælder", "forældre")) else "Andre"

    on_behalf_of_name_1 = data.get("text1")
    on_behalf_of_phone_1 = data.get("text2")

    on_behalf_of_name_2 = data.get("text3")
    on_behalf_of_phone_2 = data.get("text4")

    who = data.get("text6")

    on_behalf_of_text = (
        f"{who}\n {on_behalf_of_name_1}\n {on_behalf_of_phone_1}" if who
        else f"Forældre\n {on_behalf_of_name_1}\n {on_behalf_of_phone_1}\n\n{on_behalf_of_name_2}\n {on_behalf_of_phone_2}" if all([on_behalf_of_name_1, on_behalf_of_phone_1, on_behalf_of_name_2, on_behalf_of_phone_2])
        else f"Forælder\n {on_behalf_of_name_1}\n {on_behalf_of_phone_1}"
    )

    try:
        form = form_model(
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
            renewal_or_new_text="",
            on_behalf_of_relation=on_behalf_of_relation,
            on_behalf_of_name=on_behalf_of_name_1,
            on_behalf_of_phone=on_behalf_of_phone_1,
            on_behalf_of_text=on_behalf_of_text,

        )
    except Exception:
        logger.exception(f"Failed to prepare {form_name} form")
        return False

    try:
        db.session.add(form)
        db.session.commit()
    except Exception:
        logger.exception(f"Failed to save {form_name} form")
        db.session.rollback()
        return False
    return True


HJAELPEMIDDEL_HANDLERS = {
    "personligt_hjaelpemiddel": personligt_hjaelpemiddel,
    "staastoettestol": sel_112_113_113b_116,
    "elscooter": sel_112_113_113b_116,
    "servicehund": sel_112_113_113b_116,
    "kommunikationshjaelpemiddel": sel_112_113_113b_116,
    "hjaelpemiddel_andre_typer_af_hjaelpemidler": sel_112_113_113b_116,
    "hjaelpemiddel_til_barn": hjaelpemiddel_barn,
    "stoette_til_bil": sel_114,
    "saerlig_indretning_af_bil_koerekort": sel_114,
    "boligindretning": sel_112_113_113b_116,
    "personligt_hjaelpemiddel__kopi__test": personligt_hjaelpemiddel,  # Test form for testing purposes, should be removed in production
    "staastoettestol__kopi__test": sel_112_113_113b_116,  # Test form for testing purposes, should be removed in production
    "elscooter__kopi__test": sel_112_113_113b_116,  # Test form for testing purposes, should be removed in production
    "servicehund__kopi__test": sel_112_113_113b_116,  # Test form for testing purposes, should be removed in production
    "kommunikationshjaelpemiddel__kopi__test": sel_112_113_113b_116,  # Test form for testing purposes, should be removed in production
    "hjaelpemiddel_andre_typer_af_hjaelpemidler__kopi__test": sel_112_113_113b_116,  # Test form for testing purposes, should be removed in production
    "stoette_til_bil__kopi__test": sel_114,  # Test form for testing purposes, should be removed in production
    "hjaelpemiddel_til_barn__kopi__test": hjaelpemiddel_barn,  # Test form for testing purposes, should be removed in production
    "saerlig_indretning_af_bil_koerekort__kopi__test": sel_114,  # Test form for testing purposes, should be removed in production
    "boligindretning__kopi__test": sel_112_113_113b_116,  # Test form for testing purposes, should be removed in production
}
