from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from fastapi_backend.schema.campaign import CampaignStatus

from .base import Base


class Campaign(Base):
    __tablename__ = "campaign"
    __table_args__ = (UniqueConstraint("owner", "owner_ip_address", "name"),)
    id = Column(String, primary_key=True, index=True)
    owner = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    project = Column(String, ForeignKey("project.id"), index=True)
    num_sources = Column(Integer, nullable=False)
    corpus_target = Column(String)
    campaign_inputs = relationship(
        "CampaignInput", back_populates="campaign", cascade="all, delete-orphan"
    )
    instrumentation_metadata = Column(Text, nullable=True)
    map_to_original_source = Column(Boolean, nullable=True)
    status = Column(Enum(CampaignStatus), nullable=False, index=True)
    submitted_at = Column(
        DateTime, default=lambda x: datetime.now(), nullable=False, index=True
    )
    started_at = Column(DateTime, index=True)
    stopped_at = Column(DateTime, index=True)
    error = Column(String)
    deleted = Column(Boolean, default=False, index=True)
    public = Column(Boolean, default=False, index=True)
    lock = Column(Boolean, nullable=False, default=False, index=True)
    postprocessor_error_count = Column(Integer, nullable=False, default=0)
    postprocessor_last_run_start = Column(
        DateTime, default=lambda x: datetime.now(), nullable=False, index=True
    )
    quick_check = Column(Boolean, default=False, nullable=False, index=True)
    foundry_tests = Column(Boolean, default=False)
    foundry_tests_list = Column(String)
    report_usage = Column(Boolean, default=False)
    owner_ip_address = Column(String, index=True)
