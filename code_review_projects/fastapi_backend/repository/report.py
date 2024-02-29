import hashlib
import json
from typing import Optional

from mythx_models.response import VulnerabilityStatistics
from sqlalchemy.orm import Session

from fastapi_backend.models import ReportModel
from fastapi_backend.schema import CampaignReportedMetrics, Report, ReportInput

from .db import Session as DBSession
from .exceptions import handle_db_exceptions


class ReportRepository:
    @staticmethod
    @handle_db_exceptions()
    def create(campaign_id: str, report_input: ReportInput) -> Report:
        report = ReportModel(
            campaign_id=campaign_id,
            vulnerabilities_high=report_input.vulnerability_statistics.high,
            vulnerabilities_medium=report_input.vulnerability_statistics.medium,
            vulnerabilities_low=report_input.vulnerability_statistics.low,
            vulnerabilities_none=report_input.vulnerability_statistics.none,
            issued_at=report_input.issued_at,
            run_time=report_input.run_time,
        )
        with DBSession() as db:  # type: Session
            db.add(report)
            db.commit()
            return Report(
                id=report.id,
                campaign_id=report.campaign_id,
                vulnerability_statistics=VulnerabilityStatistics(
                    high=report.vulnerabilities_high,
                    medium=report.vulnerabilities_medium,
                    low=report.vulnerabilities_low,
                    none=report.vulnerabilities_none,
                ),
                issued_at=report.issued_at,
                run_time=report.run_time,
            )

    @staticmethod
    @handle_db_exceptions()
    def update(campaign_id: str, report_update: ReportInput) -> Report:
        with DBSession() as db:  # type: Session
            report: ReportModel = (
                db.query(ReportModel).filter_by(campaign_id=campaign_id).one()
            )
            report.vulnerabilities_high = report_update.vulnerability_statistics.high
            report.vulnerabilities_medium = (
                report_update.vulnerability_statistics.medium
            )
            report.vulnerabilities_low = report_update.vulnerability_statistics.low
            report.vulnerabilities_none = report_update.vulnerability_statistics.none
            report.issued_at = report_update.issued_at
            report.run_time = report_update.run_time
            db.commit()
            return Report(
                id=report.id,
                campaign_id=report.campaign_id,
                vulnerability_statistics=VulnerabilityStatistics(
                    high=report.vulnerabilities_high,
                    medium=report.vulnerabilities_medium,
                    low=report.vulnerabilities_low,
                    none=report.vulnerabilities_none,
                ),
                issued_at=report.issued_at,
                run_time=report.run_time,
            )

    @staticmethod
    @handle_db_exceptions()
    def delete(campaign_id: str) -> None:
        with DBSession() as db:  # type: Session
            report = (
                db.query(ReportModel).filter_by(campaign_id=campaign_id).one_or_none()
            )
            if not report:
                return
            db.delete(report)
            db.commit()

    @staticmethod
    @handle_db_exceptions()
    def get(campaign_id: str) -> Optional[Report]:
        with DBSession() as db:  # type: Session
            report = (
                db.query(ReportModel).filter_by(campaign_id=campaign_id).one_or_none()
            )
            if not report:
                return None
            return Report(
                id=report.id,
                campaign_id=report.campaign_id,
                vulnerability_statistics=VulnerabilityStatistics(
                    high=report.vulnerabilities_high,
                    medium=report.vulnerabilities_medium,
                    low=report.vulnerabilities_low,
                    none=report.vulnerabilities_none,
                ),
                issued_at=report.issued_at,
                run_time=report.run_time,
            )

    @staticmethod
    @handle_db_exceptions()
    def get_metrics(campaign_id: str) -> Optional[CampaignReportedMetrics]:
        with DBSession() as db:  # type: Session
            metrics = (
                db.query(
                    ReportModel.run_time,
                    ReportModel.vulnerabilities_high,
                    ReportModel.vulnerabilities_medium,
                    ReportModel.vulnerabilities_low,
                    ReportModel.vulnerabilities_none,
                )
                .filter_by(campaign_id=campaign_id)
                .one_or_none()
            )
            if not metrics:
                return None
            return CampaignReportedMetrics(
                vulnerability_statistics=VulnerabilityStatistics(
                    high=metrics[1],
                    medium=metrics[2],
                    low=metrics[3],
                    none=metrics[4],
                ),
                run_time=metrics[0],
            )

    @staticmethod
    def list():
        pass

    @staticmethod
    @handle_db_exceptions()
    def hash(campaign_id: str) -> str:
        with DBSession() as db:  # type: Session
            result = (
                db.query(ReportModel.issued_at)
                .filter_by(campaign_id=campaign_id)
                .one_or_none()
            )

            if result is not None:
                result = result[0].isoformat()
            return hashlib.sha1(json.dumps(result).encode("utf-8")).hexdigest()
