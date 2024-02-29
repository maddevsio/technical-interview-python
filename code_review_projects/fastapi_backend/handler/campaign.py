import os.path
import tempfile
from datetime import datetime
from typing import List, Optional, Union
from external_services.campaign_inputs import CampaignInputsRepository
from external_services.campaign_inputs.schema import CampaignInput
from external_services.campaign_metadata import CampaignMetadataRepository
from external_services.report import CampaignReportRepository
from fastapi import APIRouter, Depends, Header, Response, Security
from fastapi import status as http_status
from fastapi.responses import StreamingResponse
from fastapi_auth0 import Auth0User
from mythx_models.response.detected_issues import IssueReport
from starlette.requests import Request

from fastapi_backend.config import ApplicationSettings
from fastapi_backend.repository import (
    CampaignRepository,
    CompositeRepository,
    ReportRepository,
)
from fastapi_backend.repository.exceptions import DBError
from fastapi_backend.schema import (
    Campaign,
    CampaignResponse,
    CampaignStatus,
    CampaignUpdateInput,
    PaginatedResponse,
    PaginationParams,

)
from fastapi_backend.utils.auth import (
    AllowedPermissions,
    AnonymousUserAuth,
    OptionalAuth,
    auth,
    authenticate,
    is_anonymous_user,
)
from fastapi_backend.utils.cache import ETag, cache_headers
from fastapi_backend.utils.campaign import process_request, read_body, select_encoding
from fastapi_backend.utils.exceptions import HTTPException
from fastapi_backend.utils.id import generate_uid
from fastapi_backend.utils.stream import process

router = APIRouter()

settings = ApplicationSettings()


@router.post(
    "/",
    response_model=Campaign,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def create_campaign(
    request: Request,
    start_immediately: bool = True,
    user: Auth0User = Security(AnonymousUserAuth),
):
    if not settings.feature_anonymous_campaign_submissions and is_anonymous_user(user):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Authentication required",
        )

    client_ip_address = request.headers.get("X-Forwarded-For", None)

    campaign_id = generate_uid("cmp")

    temp_dir = tempfile.TemporaryDirectory()
    file_path = f"{temp_dir.name}/campaign_{campaign_id}.json"

    try:
        await process_request(file_path, request)

        with open(file_path, "r") as f:
            campaign, params = await process(
                campaign_id,
                user.id,
                f,
                ip_address=client_ip_address,
                no_corpus_target=True if is_anonymous_user(user) else False,
                only_default_project=True if is_anonymous_user(user) else False,
            )

            if is_anonymous_user(user):
                campaign = __share_campaign(campaign_id)

            return (
                await __start_campaign(
                    campaign_id,
                    user,
                    params,
                    client_ip_address,
                )
                if start_immediately
                else campaign
            )
    except Exception as e:
        if (
            os.path.exists(file_path)
            and not isinstance(e, HTTPException)
            and not isinstance(e, DBError)
        ):
            await CampaignMetadataRepository.get_instance().save_metadata(
                campaign_id, "body", json_stream=read_body(file_path)
            )
        if isinstance(e, ValueError):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"There was an error parsing the payload: {str(e)}",
            ) from e
        raise
    finally:
        temp_dir.cleanup()


@router.get(
    "/",
    response_model=PaginatedResponse[CampaignResponse],
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
def list_campaigns(
    params: PaginationParams = Depends(),
    status: Optional[CampaignStatus] = None,
    project: Optional[str] = None,
    user: Auth0User = Security(auth.get_user),
) -> PaginatedResponse[CampaignResponse]:
    campaigns = CompositeRepository.list_full_campaigns(
        params, project, owner=user.id, status=status
    )
    return PaginatedResponse.construct(
        items=campaigns.items,
        total=campaigns.total,
    )


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
def get_campaign(
    campaign_id: str,
    response: Response,
    user: Optional[Auth0User] = Security(OptionalAuth),
    etags: List[str] = Depends(ETag()),
) -> Union[Response, CampaignResponse]:
    if not user:
        campaign_exists = CampaignRepository.exists(campaign_id, public=True)
    else:
        campaign_exists = CampaignRepository.exists(campaign_id, owner=user.id)

    if not campaign_exists:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )

    campaign_hash = CampaignRepository.hash(campaign_id=campaign_id)
    if campaign_hash in etags:
        return Response(
            status_code=http_status.HTTP_304_NOT_MODIFIED,
            headers=cache_headers(campaign_hash),
        )

    response.headers.update(cache_headers(campaign_hash))
    return CompositeRepository.get_full_campaign(campaign_id)


@router.get(
    "/{campaign_id}/input",
    response_model=List[CampaignInput],
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def get_campaign_input(
    campaign_id: str,
    user: Optional[Auth0User] = Security(OptionalAuth),
    accept_encoding: Optional[str] = Header(None),
):
    if not user:
        campaign_exists = CampaignRepository.exists(campaign_id, public=True)
    else:
        campaign_exists = CampaignRepository.exists(campaign_id, owner=user.id)
    if not campaign_exists:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )

    _cache_headers = {
        "Cache-Control": "public, max-age=86400",
    }
    _format, selected_encoding, headers = select_encoding(accept_encoding)

    return StreamingResponse(
        # compressed encoding
        await CampaignInputsRepository.get_instance().get_campaign_inputs_chunks(
            campaign_id, _format=_format
        )
        if _format
        # identity encoding
        else await CampaignInputsRepository.get_instance().stream_campaign_inputs(
            campaign_id
        ),
        headers=_cache_headers | headers,
    )


@router.get(
    "/{campaign_id}/issues",
    response_model=List[IssueReport],
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def get_campaign_issues(
    campaign_id: str,
    user: Optional[Auth0User] = Security(OptionalAuth),
    etags: List[str] = Depends(ETag()),
    accept_encoding: Optional[str] = Header(None),
):
    report_hash = ReportRepository.hash(campaign_id)
    if report_hash in etags:
        return Response(
            status_code=http_status.HTTP_304_NOT_MODIFIED,
            headers=cache_headers(report_hash),
        )
    if not user:
        campaign_exists = CampaignRepository.exists(campaign_id, public=True)
    else:
        campaign_exists = CampaignRepository.exists(campaign_id, owner=user.id)
    if not campaign_exists:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )

    _format, selected_encoding, headers = select_encoding(accept_encoding)

    return StreamingResponse(
        # compressed encoding
        await CampaignReportRepository.get_instance().get_issues_chunks(
            campaign_id, _format=_format
        )
        if _format
        # identity encoding
        else await CampaignReportRepository.get_instance().stream_issues(campaign_id),
        headers=cache_headers(report_hash) | headers,
    )

async def __start_campaign(
    campaign_id: str,
    user: Auth0User,
    submission_ticket: Optional[RateLimiterResult] = None,
) -> Campaign:
    campaign = CampaignRepository.get(campaign_id, owner=user.id)
    if campaign is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )
    if (campaign.status != CampaignStatus.IDLE.value) and (
        campaign.status != CampaignStatus.STOPPED.value
    ):
        return campaign

    report_usage = False
    if submission_ticket is not None:
        report_usage = submission_ticket.report_usage

    campaign = CampaignRepository.update(
        campaign.id,
        CampaignUpdateInput(
            status=CampaignStatus.STARTING,
            started_at=None,
            stopped_at=None,
            report_usage=report_usage,
        ),
    )
    return campaign


@router.post(
    "/{campaign_id}/start",
    response_model=Campaign,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def start_campaign(
    campaign_id: str,
    request: Request,
    user: Auth0User = Security(AllowedPermissions("admin")),
) -> Campaign:
    client_ip_address = request.headers.get("X-Forwarded-For", None)
    return await __start_campaign(
        campaign_id, user, client_ip_address=client_ip_address
    )


@router.post(
    "/{campaign_id}/stop",
    response_model=Campaign,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def stop_campaign(
    campaign_id: str,
    user: Auth0User = Security(authenticate),
) -> Campaign:
    if user.id[-8:] == "@clients":  # M2M Client
        if not user.permissions or "campaign:stop" not in user.permissions:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to stop campaign",
            )
        campaign = CampaignRepository.get(campaign_id)
    else:
        campaign = CampaignRepository.get(campaign_id, owner=user.id)

    if campaign is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )
    if (
        campaign.status != CampaignStatus.RUNNING.value
        and campaign.status != CampaignStatus.STARTING.value
    ):
        return campaign

    return CampaignRepository.update(
        campaign.id,
        CampaignUpdateInput(
            status=CampaignStatus.STOPPING,
            stopped_at=datetime.now(),
        ),
    )


def __share_campaign(campaign_id: str) -> Campaign:
    return CampaignRepository.update(campaign_id, CampaignUpdateInput(public=True))


@router.post(
    "/{campaign_id}/share",
    response_model=Campaign,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def share_campaign(
    campaign_id: str,
    user: Auth0User = Security(auth.get_user),
) -> Campaign:
    if not CampaignRepository.exists(campaign_id, owner=user.id):
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )
    return __share_campaign(campaign_id)


@router.delete(
    "/{campaign_id}/share",
    response_model=Campaign,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def unshare_campaign(
    campaign_id: str,
    user: Auth0User = Security(auth.get_user),
) -> Campaign:
    if not CampaignRepository.exists(campaign_id, owner=user.id):
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )
    return CampaignRepository.update(campaign_id, CampaignUpdateInput(public=False))
