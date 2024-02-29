from datetime import datetime, timedelta

from mythx_models.response import VulnerabilityStatistics
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import coalesce

from fastapi_backend.models import CampaignModel, FullCampaignView, ReportModel

from ..schema import (
    CampaignCorpus,
    CampaignProject,
    CampaignResponse,
    CampaignStatus,
    PaginatedResult,
    PaginationParams,
)
from .db import Session as DBSession
from .exceptions import handle_db_exceptions


class CompositeRepository:
    @staticmethod
    def construct_campaign_response(campaign: FullCampaignView) -> CampaignResponse:
        project = None
        if campaign.project:
            project = CampaignProject.construct(
                id=campaign.project, name=campaign.project_name
            )
        vuln_stats = VulnerabilityStatistics.construct(
            high=campaign.vulnerabilities_high or 0,
            medium=campaign.vulnerabilities_medium or 0,
            low=campaign.vulnerabilities_low or 0,
            none=campaign.vulnerabilities_none or 0,
        )

        return CampaignResponse.construct(
            id=campaign.id,
            name=campaign.name,
            owner=campaign.owner,
            public=campaign.public,
            corpus=CampaignCorpus.construct(target=campaign.corpus_target),
            num_sources=campaign.num_sources,
            status=CampaignStatus(campaign.status.lower()),
            submitted_at=campaign.submitted_at,
            started_at=campaign.started_at,
            stopped_at=campaign.stopped_at,
            error=campaign.error,
            project=project,
            vulnerability_statistics=vuln_stats,
            run_time=campaign.run_time or 0,
            time_limit=campaign.time_limit,
        )

    @classmethod
    @handle_db_exceptions()
    def get_full_campaign(cls, campaign_id: str) -> CampaignResponse | None:
        with DBSession() as db:  # type: Session
            campaign: FullCampaignView = (
                db.query(FullCampaignView)
                .filter(FullCampaignView.id == campaign_id)
                .one_or_none()
            )
            if campaign is None:
                return None
            return cls.construct_campaign_response(campaign)

    @classmethod
    @handle_db_exceptions()
    def list_full_campaigns(
        cls,
        params: PaginationParams,
        project: str | None = None,
        status: CampaignStatus | list[CampaignStatus] | None = None,
        owner: str | None = None,
    ) -> PaginatedResult[CampaignResponse]:
        with DBSession() as db:  # type: Session
            query = db.query(FullCampaignView).filter(FullCampaignView.deleted == False)
            if owner:
                query = query.filter(FullCampaignView.owner == owner)
            if project:
                query = query.filter(FullCampaignView.project == project)
            if status:
                if type(status) != list:
                    status = [status]
                query = query.filter(
                    FullCampaignView.status.in_([s.name for s in status])
                )
            query = (
                query.order_by(FullCampaignView.submitted_at.desc())
                .offset(params.offset)
                .limit(params.limit)
            )
            total = query.count()
            return PaginatedResult[CampaignResponse].construct(
                items=[cls.construct_campaign_response(campaign) for campaign in query],
                total=total,
                limit=params.limit,
                offset=params.offset,
            )

    @staticmethod
    @handle_db_exceptions()
    def get_stalled_campaigns(report_timeout: int) -> list[str]:
        with DBSession() as db:
            stalled_campaign_ids = (
                db.query(CampaignModel.id)
                .outerjoin(ReportModel, CampaignModel.id == ReportModel.campaign_id)
                .filter(
                    CampaignModel.status == CampaignStatus.RUNNING.name,
                    coalesce(ReportModel.issued_at, CampaignModel.started_at)
                    < (datetime.utcnow() - timedelta(seconds=report_timeout)),
                )
                .all()
            )
            if stalled_campaign_ids:
                stalled_campaign_ids = [id for (id,) in stalled_campaign_ids]
            return stalled_campaign_ids or []
