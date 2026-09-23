from datetime import date
from enum import Enum

from sqlalchemy import String, Date, Text, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from extensions import db
from utils.config import XFLOW_NEXUS_HJAELPEMIDDEL_DB_TABLE


class HjaelpemiddelStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class HjaelpemiddelBase(db.Model):
    __abstract__ = True
    __table_args__ = {"schema": XFLOW_NEXUS_HJAELPEMIDDEL_DB_TABLE}

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[HjaelpemiddelStatus] = mapped_column(
        SqlEnum(HjaelpemiddelStatus, name="hjaelpemiddel_status"),
        nullable=False,
        default=HjaelpemiddelStatus.RECEIVED,
    )
    cpr: Mapped[str] = mapped_column(String(11), nullable=False)
    form_date: Mapped[date] = mapped_column(Date)
    form_doc_name: Mapped[str] = mapped_column(String(255), nullable=False)
    form_pdf_base64: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_doc_name: Mapped[str] = mapped_column(String(255), nullable=False)
    attachments: Mapped[list] = mapped_column(JSONB, nullable=True, default=list)

    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    can_collect_data: Mapped[bool] = mapped_column(nullable=False, default=False)
    for_another: Mapped[bool] = mapped_column(nullable=False, default=False)
    reason_text: Mapped[str] = mapped_column(String(255), nullable=False)
    renewal_or_new_text: Mapped[str] = mapped_column(String(255), nullable=False)

    on_behalf_of_relation: Mapped[str] = mapped_column(String(255), nullable=True)
    on_behalf_of_name: Mapped[str] = mapped_column(String(255), nullable=True)
    on_behalf_of_phone: Mapped[str] = mapped_column(String(255), nullable=True)
    on_behalf_of_text: Mapped[str] = mapped_column(String(255), nullable=True)


class PersonligtHjaelpemiddel(HjaelpemiddelBase):
    __tablename__ = "personligt_hjaelpemiddel"


class Staastoettestol(HjaelpemiddelBase):
    __tablename__ = "staastoettestol"


class Elscooter(HjaelpemiddelBase):
    __tablename__ = "elscooter"


class Servicehund(HjaelpemiddelBase):
    __tablename__ = "servicehund"


class Kommunikationshjaelpemiddel(HjaelpemiddelBase):
    __tablename__ = "kommunikationshjaelpemiddel"


class HjaelpemiddelAndreTyperAfHjaelpemidler(HjaelpemiddelBase):
    __tablename__ = "hjaelpemiddel_andre_typer_af_hjaelpemidler"


class HjaelpemiddelTilBarn(HjaelpemiddelBase):
    __tablename__ = "hjaelpemiddel_til_barn"


class StoetteTilBil(HjaelpemiddelBase):
    __tablename__ = "stoette_til_bil"
    type_text: Mapped[str] = mapped_column(String(255), nullable=False)


class SaerligIndretningAfBilKoerekort(HjaelpemiddelBase):
    __tablename__ = "saerlig_indretning_af_bil_koerekort"
    type_text: Mapped[str] = mapped_column(String(255), nullable=False)


class Boligindretning(HjaelpemiddelBase):
    __tablename__ = "boligindretning"
