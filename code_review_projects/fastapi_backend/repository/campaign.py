import hashlib
import json
from typing import List, Optional, Union

from sqlalchemy import or_, select
from sqlalchemy.orm import Query, Session
from ujson import encode

from fastapi_backend.models import CampaignModel, ReportModel
from fastapi_backend.schema import (
    Campaign,
    CampaignBase,
    CampaignStatus,
    CampaignUpdateInput,
    PaginatedResult,
    PaginationParams,
)
from fastapi_backend.utils.id import generate_uid

from .db import Session as DBSession
from .db import WrongQueryError
from .exceptions import handle_db_exceptions


def _uvd(name):
    return f'name "{name}" is already used in another campaign'


def get_name(*args, **kwargs):
    if "campaign_input" in kwargs:
        return _uvd(kwargs["campaign_input"].name)
    if len(args) > 0:
        return _uvd(args[0].name)
    return "name is already used in another campaign"


class CampaignRepository:
    running_campaigns = [CampaignStatus.RUNNING, CampaignStatus.STARTING]
    all_campaigns_without_error = [
        CampaignStatus.RUNNING,
        CampaignStatus.STARTING,
        CampaignStatus.STOPPED,
        CampaignStatus.IDLE,
        CampaignStatus.STOPPING,
    ]

    @staticmethod
    @handle_db_exceptions(unique_violation_description=get_name)
    def create(
        campaign_input: CampaignBase, campaign_id: Optional[str] = None
    ) -> Campaign:
        campaign = CampaignModel(
            id=campaign_id or generate_uid(prefix="cmp"),
            owner=campaign_input.owner,
            public=campaign_input.public,
            name=campaign_input.name,
            project=campaign_input.project,
            corpus_target=campaign_input.corpus.target
            if campaign_input.corpus
            else None,
            status=campaign_input.status,
            submitted_at=campaign_input.submitted_at,
            num_sources=campaign_input.num_sources,
            instrumentation_metadata=None
            if campaign_input.instrumentation_metadata is None
            else encode(campaign_input.instrumentation_metadata),
            map_to_original_source=campaign_input.map_to_original_source,
            started_at=campaign_input.started_at,
            stopped_at=campaign_input.stopped_at,
            quick_check=campaign_input.quick_check,
            foundry_tests=campaign_input.foundry_tests,
            foundry_tests_list=None
            if campaign_input.foundry_tests_list is None
            else encode(campaign_input.foundry_tests_list),
            report_usage=campaign_input.report_usage,
            owner_ip_address=campaign_input.owner_ip_address,
        )
        with DBSession() as db:  # type: Session
            db.add(campaign)
            db.commit()
            return Campaign.from_orm(campaign)

    @staticmethod
    @handle_db_exceptions(
        unique_violation_description=lambda *args, **kwargs: _uvd(
            kwargs.get("campaign_update", args[1]).name
        ),
    )
    def update(
        campaign_id: str, campaign_update: CampaignUpdateInput
    ) -> Optional[Campaign]:
        with DBSession() as db:  # type: Session
            campaign = db.query(CampaignModel).get(campaign_id)
            updated_fields = campaign_update.dict(exclude_unset=True)
            for field, value in updated_fields.items():
                setattr(campaign, field, value)
            db.commit()
            return Campaign.from_orm(campaign)

    @staticmethod
    @handle_db_exceptions()
    def delete(campaign_id: str) -> None:
        with DBSession() as db:  # type: Session
            db.query(CampaignModel).filter(CampaignModel.id == campaign_id).update(
                {CampaignModel.deleted: True}, synchronize_session=False
            )
            db.commit()

    @staticmethod
    @handle_db_exceptions()
    def add_to_default_project(project_id: str, default_project_id: str):
        with DBSession() as db:  # type: Session
            campaigns = db.query(CampaignModel).filter(
                CampaignModel.project == project_id
            )
            for campaign in campaigns:
                campaign.project = default_project_id
            db.commit()

    @staticmethod
    @handle_db_exceptions()
    def get(
        campaign_id: Optional[str] = None,
        owner: Optional[str] = None,
        public: Optional[bool] = None,
        status: Optional[CampaignStatus] = None,
        name: Optional[str] = None,
    ) -> Optional[Campaign]:
        if not campaign_id and not name:
            raise WrongQueryError("No `campaign_id` nor `name` was provided")
        with DBSession() as db:  # type: Session
            query: Query = db.query(CampaignModel).filter(
                CampaignModel.deleted == False,
            )
            if campaign_id:
                query = query.filter(CampaignModel.id == campaign_id)
            if owner:
                query = query.filter(
                    or_(CampaignModel.owner == owner, CampaignModel.public == True)
                )
            if public:
                query = query.filter(CampaignModel.public == public)
            if status:
                query = query.filter(CampaignModel.status == status)
            if name:
                query = query.filter(CampaignModel.name == name)
            campaign = query.one_or_none()
            if not campaign:
                return None
            return Campaign.from_orm(campaign)

    @staticmethod
    @handle_db_exceptions()
    def list(
        params: PaginationParams,
        project: Optional[str] = None,
        status: Optional[Union[CampaignStatus, List[CampaignStatus]]] = None,
        owner: Optional[str] = None,
        owner_ip_address: str | None = None,
    ) -> PaginatedResult[Campaign]:
        with DBSession() as db:  # type: Session
            query = db.query(CampaignModel).filter(CampaignModel.deleted == False)
            if owner:
                query = query.filter(CampaignModel.owner == owner)
            if project:
                query = query.filter(CampaignModel.project == project)
            if status:
                if type(status) != list:
                    status = [status]
                query = query.filter(CampaignModel.status.in_([s.name for s in status]))
            if owner_ip_address:
                query = query.filter(CampaignModel.owner_ip_address == owner_ip_address)
            query = (
                query.order_by(CampaignModel.submitted_at.desc())
                .offset(params.offset)
                .limit(params.limit)
            )
            total = query.count()
            # TODO: query only needed fields
            items = [Campaign.from_orm(campaign) for campaign in query]
            return PaginatedResult[Campaign](
                items=items,
                total=total,
                limit=params.limit,
                offset=params.offset,
            )

    @staticmethod
    @handle_db_exceptions()
    def exists(
        campaign_id: str, owner: Optional[str] = None, public: Optional[bool] = None
    ) -> bool:
        filters = [CampaignModel.id == campaign_id]
        if owner:
            filters.append(
                or_(CampaignModel.owner == owner, CampaignModel.public == True)
            )
        if public is not None:
            filters.append(CampaignModel.public == public)
        stmt = select(CampaignModel).where(*filters).exists().select()
        with DBSession() as db:  # type: Session
            result = db.execute(stmt).scalar()
            return result

    @staticmethod
    @handle_db_exceptions()
    def count(
        status: Optional[Union[CampaignStatus, List[CampaignStatus]]] = None,
        owner: Optional[str] = None,
        owner_ip_address: str | None = None,
    ) -> int:
        with DBSession() as db:  # type: Session
            # we count deleted campaigns too, because user can delete campaigns
            # and submit new ones without hitting the subscription limits
            query = db.query(CampaignModel.id)
            if owner:
                query = query.filter(CampaignModel.owner == owner)
            if status:
                if type(status) != list:
                    status = [status]
                query = query.filter(CampaignModel.status.in_([s.name for s in status]))
            if owner_ip_address:
                query = query.filter(CampaignModel.owner_ip_address == owner_ip_address)
            return query.count()

    @staticmethod
    @handle_db_exceptions()
    def hash(campaign_id: str):
        with DBSession() as db:  # type: Session
            query = (
                db.query(CampaignModel.status, ReportModel.issued_at)
                .filter(CampaignModel.id == campaign_id, CampaignModel.deleted == False)
                .outerjoin(ReportModel)
            )
            _res = query.one_or_none()
            if _res is None:
                return None
            result = list(_res)
            if result[1] is not None:
                result[1] = result[1].isoformat()
            return hashlib.sha1(json.dumps(result).encode("utf-8")).hexdigest()
