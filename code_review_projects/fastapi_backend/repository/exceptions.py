import functools
import sys
from typing import Callable, Optional, ParamSpec, Tuple, TypeVar, Union

from sqlalchemy.exc import IntegrityError

P = ParamSpec("P")
R = TypeVar("R")


class DBError(Exception):
    def __init__(
        self,
        detail: str,
        orig_error: Optional[Tuple[any, any, any]] = None,
        status_code=500,
    ):
        super(DBError, self).__init__(detail)
        self.detail = detail
        self.error = "DBError"
        self.orig_error = orig_error
        self.status_code = status_code
        self.handled = False


class UniqueConstraintViolation(DBError):
    def __init__(self, *args, **kwargs):
        super(UniqueConstraintViolation, self).__init__(*args, **kwargs)
        self.error = "UniqueConstraintViolation"
        self.handled = True


def __prepare_description(desc: Union[str, Callable[..., str]], *args, **kwargs) -> str:
    try:
        if callable(desc):  # function to generate custom error description
            return desc(*args, **kwargs)
        return desc
    except:
        return "DB Error"


def handle_db_exceptions(
    description: Optional[
        Union[str, Callable[..., str]]
    ] = "There was an error with DB operations",
    unique_violation_description: Optional[
        Union[str, Callable[..., str]]
    ] = "Unique constraint is violated",
):
    def factory(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return f(*args, **kwargs)
            except IntegrityError as e:
                error_code = getattr(e.orig, "pgcode", -1)
                if str(error_code) == "23505":  # UniqueViolation
                    raise UniqueConstraintViolation(
                        detail=__prepare_description(
                            unique_violation_description, *args, **kwargs
                        ),
                        status_code=400,
                        orig_error=sys.exc_info(),
                    )
                raise DBError(
                    detail=__prepare_description(description, *args, **kwargs),
                    orig_error=sys.exc_info(),
                )
            except:
                raise DBError(
                    detail=__prepare_description(description, *args, **kwargs),
                    orig_error=sys.exc_info(),
                )

        return wrapper

    return factory
