from typing import List, Optional

from fastapi import Header


class ETag:
    def __call__(
        self,
        if_none_match: Optional[str] = Header(None),
    ) -> List[str]:
        etags: List[str] = []
        if if_none_match:
            etags.extend(
                [etag.strip() for etag in if_none_match.split(",")],
            )
        if len(etags) == 1 and etags[0] == "*":
            return []
        return etags


def cache_headers(etag: str):
    return {"ETag": etag, "Cache-Control": "no-cache"}
