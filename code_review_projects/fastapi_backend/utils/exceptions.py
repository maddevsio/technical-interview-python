from fastapi import HTTPException as __HTTPException


class HTTPException(__HTTPException):
    def __init__(self, error=None, *args, **kwargs):
        super(HTTPException, self).__init__(*args, **kwargs)
        self.error = error


class ReportTimeoutError(Exception):
    def __init__(self, campaign_id: str):
        super(ReportTimeoutError, self).__init__(
            f"Report timeout for campaign {campaign_id}"
        )
        self.campaign_id = campaign_id


class ConcurrentRequestError(HTTPException):
    pass


class ProjectNotFoundError(HTTPException):
    def __init__(self):
        super(ProjectNotFoundError, self).__init__(
            status_code=400,
            detail="Project not found",
        )


class FaaSValidationError(HTTPException):
    def __init__(self, errors):
        super(FaaSValidationError, self).__init__(
            status_code=422,
            detail=errors,
        )
