from datetime import datetime

from mythx_models.response import VulnerabilityStatistics
from pydantic import BaseModel


class ReportInput(BaseModel):
    vulnerability_statistics: VulnerabilityStatistics
    issued_at: datetime
    run_time: int

    class Config:
        allow_population_by_field_name = True


class Report(ReportInput):
    id: int
    campaign_id: str

    class Config:
        orm_mode = True


class CampaignReportedMetrics(BaseModel):
    vulnerability_statistics: VulnerabilityStatistics
    run_time: int

    class Config:
        orm_mode = True
