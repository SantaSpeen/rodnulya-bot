from enum import StrEnum, IntEnum


class ApiErrors(StrEnum):
    INTERNAL_SERVER_ERROR = "Internal server error"


class ApiErrorCodes(IntEnum):
    INTERNAL_SERVER_ERROR = 1

def _get_code(name: str) -> int:
    try:
        return ApiErrorCodes[name].value
    except KeyError:
        return ApiErrorCodes.INTERNAL_SERVER_ERROR.value
