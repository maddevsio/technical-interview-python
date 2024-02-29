from typing import Iterator

from faas_services.serde import SerDesBackends
from fastapi import Request


async def process_request(file_path: str, request: Request):
    # stream the request body to a file, because json_stream.load() can only use sync generators
    with open(file_path, "wb") as f:
        async for chunk in request.stream():
            f.write(chunk)


def read_body(file_path: str) -> Iterator[bytes]:
    # read the file contents to a dict
    with open(file_path, "rb") as f:
        while data := f.read(1024 * 1024):  # read 1MB at a time
            yield data


def select_encoding(
    accept_encoding: str | None = None,
) -> tuple[SerDesBackends | None, str, dict[str, str]]:
    _format = None
    selected_encoding = "identity"

    # TODO: add support for quality values weighting
    if accept_encoding:
        supported_encodings = [
            enc.strip().lower().split(";")[0] for enc in accept_encoding.split(",")
        ]
        if "br" in supported_encodings or "*" in supported_encodings:
            _format = SerDesBackends.BROTLI
            selected_encoding = "br"
        elif "gzip" in supported_encodings:
            _format = SerDesBackends.GZIP
            selected_encoding = "gzip"
        else:
            # we don't support deflate, compress yet, so we default to identity
            pass

    headers = {
        "Content-Type": "application/json",
    }
    if selected_encoding and selected_encoding != "identity":
        headers["Content-Encoding"] = selected_encoding

    return _format, selected_encoding, headers
