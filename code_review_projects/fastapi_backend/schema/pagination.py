from typing import Generic, Sequence, TypeVar

from pydantic.generics import BaseModel, GenericModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    limit: int = 10
    offset: int = 0


class PaginatedResponse(GenericModel, Generic[T]):
    items: Sequence[T]
    total: int


class PaginatedResult(GenericModel, Generic[T]):
    items: Sequence[T]
    total: int
    offset: int
    limit: int
