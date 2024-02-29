from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from faas_services.campaign_inputs.schema import CampaignInput
from mythx_models.response import VulnerabilityStatistics
from mythx_models.response.detected_issues import IssueReport
from pydantic import BaseModel, Field, root_validator
from pydantic.utils import GetterDict
from ujson import loads

from fastapi_backend.schema.corpus import CorpusInput

from .campaign_input import CampaignInputRequest
from .campaign_parameters import CampaignParametersRequest


class Source(BaseModel):
    file_index: int = Field(alias="fileIndex")
    source: str
    ast: dict[str, Any] | None


class CampaignRequestBase(BaseModel):
    name: str = ""
    parameters: CampaignParametersRequest = CampaignParametersRequest.parse_obj({})
    project: Optional[str]
    quick_check: bool = Field(False, alias="quickCheck")
    sources: Optional[Dict[str, Dict[str, Any]]]
    instrumentation_metadata: Optional[Any] = Field(alias="instrumentationMetadata")
    map_to_original_source: Optional[bool] = Field(
        alias="mapToOriginalSource",
        description="Controls whether to remap source ranges of the instrumented `source_map` to the source ranges "
        "of the original (non-instrumented) source.",
    )
    time_limit: Optional[int] = Field(
        alias="timeLimit", description="Time Limit for campaign to run in seconds"
    )
    foundry_tests: Optional[bool] = Field(False, alias="foundryTests")
    foundry_tests_list: Optional[Dict[str, Dict[str, List[str]]]] = Field(
        None, alias="foundryTestsList"
    )


class MultiContractCampaignRequest(CampaignRequestBase):
    corpus: CorpusInput
    contracts: List[CampaignInputRequest]

    @root_validator(skip_on_failure=True)
    def corpus_validator(cls, values):
        violations = []
        corpus: CorpusInput = values.get("corpus")
        if not corpus:  # there is an error
            raise ValueError("corpus is required")
        if corpus.target:  # corpus target is set so no need to check other fields
            return values
        if corpus.steps is None or len(corpus.steps) == 0:
            violations.append("corpus.steps is required")
        if values.get("quick_check", False) is False:
            if not corpus.address_under_test:
                violations.append("corpus.address-under-test is required")
        if violations:
            raise ValueError(". ".join(violations))
        return values


class CampaignRequest(BaseModel):
    name: str = ""
    project: Optional[str]
    quick_check: bool = Field(False, alias="quickCheck")
    instrumentation_metadata: Optional[Any] = Field(alias="instrumentationMetadata")
    map_to_original_source: Optional[bool] = Field(
        alias="mapToOriginalSource",
        description="Controls whether to remap source ranges of the instrumented `source_map` to the source ranges "
        "of the original (non-instrumented) source.",
    )
    time_limit: Optional[int] = Field(
        alias="timeLimit", description="Time Limit for campaign to run in seconds"
    )
    foundry_tests: Optional[bool] = Field(False, alias="foundryTests")
    foundry_tests_list: Optional[Dict[str, Dict[str, List[str]]]] = Field(
        None, alias="foundryTestsList"
    )


class CampaignStatus(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    IDLE = "idle"


class CampaignCorpus(BaseModel):
    target: Optional[str]


class CampaignGetterDict(GetterDict):
    def __getitem__(self, key: str) -> Any:
        try:
            self.get(key)
        except AttributeError as e:
            raise KeyError(key) from e

    def get(self, key: Any, default: Any = None) -> Any:
        if key == "corpus":
            target = getattr(self._obj, "corpus_target")
            if target is None:
                # LEGACY: return dict with a target=null, to not break the frontend which waits for the dict.
                # However, target field will be filtered out from the response and we end up with an empty dict ({})
                return {
                    "target": None,
                }
            return {
                "target": target,
            }
        if key == "instrumentation_metadata":
            meta = getattr(self._obj, "instrumentation_metadata")
            if meta is None:
                return None
            return loads(meta)

        if key == "foundry_tests_list":
            tests_list = getattr(self._obj, "foundry_tests_list")
            if tests_list is None:
                return None
            return loads(tests_list)
        return getattr(self._obj, key, default)


class CampaignBase(BaseModel):
    name: str
    owner: str
    public: bool = Field(False, alias="publicAccess")
    project: Optional[str] = Field(None)
    corpus: Optional[CampaignCorpus]
    num_sources: int = Field(alias="numSources")
    status: CampaignStatus
    instrumentation_metadata: Optional[Any] = Field(
        alias="instrumentationMetadata", exclude=True
    )
    map_to_original_source: Optional[bool] = Field(
        alias="mapToOriginalSource",
        description="Controls whether to remap source ranges of the instrumented `source_map` to the source ranges "
        "of the original (non-instrumented) source.",
        exclude=True,
    )
    submitted_at: datetime = Field(alias="submittedAt")
    started_at: Optional[datetime] = Field(alias="startedAt")
    stopped_at: Optional[datetime] = Field(alias="stoppedAt")
    error: Optional[str]
    quick_check: Optional[bool] = Field(False, alias="quickCheck", exclude=True)
    foundry_tests: Optional[bool] = Field(False, alias="foundryTests", exclude=True)
    foundry_tests_list: Optional[Dict[str, Dict[str, List[str]]]] = Field(
        None, alias="foundryTestsList", exclude=True
    )
    report_usage: Optional[bool] = Field(False, alias="reportUsage", exclude=True)
    owner_ip_address: Optional[str] = Field(alias="ownerIpAddress", exclude=True)

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True
        getter_dict = CampaignGetterDict


class Campaign(CampaignBase):
    id: str

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        getter_dict = CampaignGetterDict


class CampaignWithEmail(Campaign):
    owner_email: Optional[str]


class CampaignProject(BaseModel):
    id: str
    name: str


class CampaignResponse(Campaign):
    project: Optional[CampaignProject]
    vulnerability_statistics: VulnerabilityStatistics = Field(
        alias="numVulnerabilities"
    )
    run_time: int = Field(alias="runTime")
    time_limit: Optional[int] = Field(
        alias="timeLimit", description="time limit in seconds set to the campaign"
    )

    class Config:
        allow_population_by_field_name = True


class CampaignUpdateRequest(BaseModel):
    name: Optional[str]
    project: Optional[str]


class CampaignUpdateInput(CampaignUpdateRequest):
    status: Optional[CampaignStatus]
    started_at: Optional[datetime] = Field(alias="startedAt")
    stopped_at: Optional[datetime] = Field(alias="stoppedAt")
    error: Optional[str]
    public: Optional[bool]
    report_usage: Optional[bool]

    class Config:
        allow_population_by_field_name = True


class CampaignRawResponse(BaseModel):
    instrumentation_metadata: Optional[Any] = Field(alias="instrumentationMetadata")
    map_to_original_source: Optional[bool] = Field(alias="mapToOriginalSource")
    issues: List[IssueReport]
    inputs: List[CampaignInput]

    class Config:
        allow_population_by_field_name = True
