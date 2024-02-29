from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import backref, relationship

from .base import Base


class Report(Base):
    __tablename__ = "report"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(String, ForeignKey("campaign.id"), nullable=False, unique=True)
    campaign = relationship("Campaign", backref=backref("report", uselist=False))
    vulnerabilities_high = Column(Integer, default=0, nullable=False)
    vulnerabilities_medium = Column(Integer, default=0, nullable=False)
    vulnerabilities_low = Column(Integer, default=0, nullable=False)
    vulnerabilities_none = Column(Integer, default=0, nullable=False)
    issued_at = Column(DateTime, nullable=False)
    run_time = Column(Integer, default=0)
