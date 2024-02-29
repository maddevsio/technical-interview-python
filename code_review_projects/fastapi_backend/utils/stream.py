import io
from datetime import datetime

import elasticapm
import json_stream
from faas_services.campaign_inputs import CampaignInputsRepository
from faas_services.corpus import CampaignCorpusRepository

from fastapi_backend.repository import (
    CampaignInputRepository,
    CampaignParametersRepository,
    CampaignRepository,
)
from fastapi_backend.schema import (
    Campaign,
    CampaignBase,
    CampaignCorpus,
    CampaignInputBase,
    CampaignParameters,
    CampaignStatus,
)
from fastapi_backend.utils.corpus import get_target_campaign_id
from fastapi_backend.utils.exceptions import FaaSValidationError, ProjectNotFoundError
from fastapi_backend.utils.project import get_default_project, get_project
from fastapi_backend.utils.streaming import (
    CampaignProcessor,
    ConfigProcessor,
    ContractsProcessor,
    CorpusProcessor,
    ParametersProcessor,
    SourcesProcessor,
)


@elasticapm.async_capture_span()
async def process(
    campaign_id: str,
    user_id: str,
    data: io.FileIO,
    ip_address: str | None = None,
    only_default_project: bool = False,
    no_corpus_target: bool = False,
) -> tuple[Campaign, CampaignParameters]:
    stream = json_stream.load(data)
    campaign_processor = CampaignProcessor()
    sources_processor = SourcesProcessor(campaign_id)
    corpus_processor = CorpusProcessor(campaign_id)
    contracts_processor = ContractsProcessor(campaign_id)
    parameters_processor = ParametersProcessor()
    config_processor = ConfigProcessor(
        campaign_id, corpus_processor, parameters_processor
    )

    try:
        for key, value in stream.items():
            if key == "sources":
                sources_processor.process(value)
                await CampaignInputsRepository.get_instance().save_campaign_sources(
                    campaign_id=campaign_id,
                    sources_json=sources_processor.sources_stream_json(),
                    overwrite=True,
                )
                await CampaignInputsRepository.get_instance().save_campaign_sources(
                    campaign_id=campaign_id,
                    sources=sources_processor.sources_stream(with_ast=False),
                    sources_without_ast=True,
                    overwrite=True,
                )
            elif key == "contracts":
                contracts_processor.process(value)
                if contracts_processor.validation_errors:
                    raise FaaSValidationError(contracts_processor.validation_errors)
                await CampaignInputsRepository.get_instance().save_campaign_inputs(
                    campaign_id=campaign_id,
                    campaign_inputs_json=contracts_processor.inputs_stream_json(),
                    overwrite=True,
                )
            elif key == "parameters":
                parameters_processor.process(value)
                if parameters_processor.validation_errors:
                    raise FaaSValidationError(parameters_processor.validation_errors)
            elif key == "corpus":
                corpus_processor.process(value)
                if corpus_processor.validation_errors:
                    raise FaaSValidationError(corpus_processor.validation_errors)

                corpus_target = None
                if not no_corpus_target and corpus_processor.corpus.target:
                    corpus_target = get_target_campaign_id(
                        corpus_processor.corpus.target, user_id
                    )

                corpus_processor.corpus_target = corpus_target

                if corpus_target and not corpus_processor.has_suggested_seed_seqs:
                    # corpus target is provided but with no fuzzing lessons (no suggested seed sequences),
                    # so we just copy the corpus
                    await CampaignCorpusRepository.get_instance().copy_corpus(
                        corpus_target, campaign_id
                    )
                elif corpus_target and corpus_processor.has_suggested_seed_seqs:
                    # fuzzing lessons are provided, so we need to merge them with the corpus target
                    target_corpus = (
                        await CampaignCorpusRepository.get_instance().stream_corpus(
                            corpus_target
                        )
                    )

                    @json_stream.streamable_list
                    def merged_corpus():
                        for i in json_stream.load(target_corpus):
                            yield json_stream.to_standard_types(i)
                        for i in corpus_processor.suggested_seed_seqs_stream:
                            yield i

                    await CampaignCorpusRepository.get_instance().save_corpus(
                        campaign_id, merged_corpus(), True
                    )
                elif not corpus_target and corpus_processor.has_suggested_seed_seqs:
                    await CampaignCorpusRepository.get_instance().save_corpus(
                        campaign_id,
                        corpus_processor.suggested_seed_seqs_stream,
                        True,
                    )
            else:
                # the rest of the keys are campaign fields
                campaign_processor.process(value, key)

        if campaign_processor.validation_errors:
            raise FaaSValidationError(campaign_processor.validation_errors)

        corpus_processor.validate()
        contracts_processor.validate()

        await CampaignCorpusRepository.get_instance().save_config(
            campaign_id, config_processor.config_stream
        )

        if not only_default_project and campaign_processor.campaign_request.project:
            project = get_project(
                campaign_processor.campaign_request.project,
                owner=user_id,
                upsert=True,
            )
            if (
                not project
            ):  # could not create a project with an id (need a name at least)
                raise ProjectNotFoundError()
            project_id = project.id
        else:
            project_id = get_default_project(user_id).id

        campaign_name = campaign_processor.campaign_request.name
        if not campaign_name:
            count = CampaignRepository.count()
            campaign_name = f"untitled_{count + 1}"

        campaign = CampaignRepository.create(
            campaign_input=CampaignBase.construct(
                owner=user_id,
                name=campaign_name,
                project=project_id,
                corpus=CampaignCorpus(target=corpus_processor.corpus_target),
                status=CampaignStatus.IDLE,
                submitted_at=datetime.now(),
                num_sources=contracts_processor.num_sources,
                instrumentation_metadata=campaign_processor.campaign_request.instrumentation_metadata,
                map_to_original_source=campaign_processor.campaign_request.map_to_original_source,
                quick_check=campaign_processor.campaign_request.quick_check,
                foundry_tests=campaign_processor.campaign_request.foundry_tests,
                foundry_tests_list=campaign_processor.campaign_request.foundry_tests_list,
                owner_ip_address=ip_address,
            ),
            campaign_id=campaign_id,
        )

        parameters = CampaignParametersRepository.create(
            campaign_id,
            parameters_processor.parameters,
            campaign_processor.campaign_request.time_limit,
        )

        CampaignInputRepository.create_bulk(
            campaign_id,
            [
                CampaignInputBase.construct(main_source_file=main_source_file)
                for main_source_file in contracts_processor.main_source_files
            ],
        )
    except Exception:
        raise
    finally:
        # TODO: remove files and DB entries if something goes wrong (i.e. rollback)
        campaign_processor.cleanup()
        sources_processor.cleanup()
        corpus_processor.cleanup()
        contracts_processor.cleanup()
        parameters_processor.cleanup()
        config_processor.cleanup()

    return campaign, parameters
