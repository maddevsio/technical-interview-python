from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB

from fastapi_backend.models import Base


class FreezeTimeParamType(Base):
    __tablename__ = "freeze_time_param_type"
    param_type = Column(String, primary_key=True)


class FreezeTimeParams(Base):
    __tablename__ = "freeze_time_params"
    param = Column(
        String, ForeignKey("freeze_time_param_type.param_type"), primary_key=True
    )
    value = Column(JSONB)
