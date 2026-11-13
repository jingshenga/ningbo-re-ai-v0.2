"""Typed failure kinds for the local media pipeline; never carry raw file paths in messages."""
from __future__ import annotations


class MediaPipelineError(RuntimeError):
    """Base error. `kind` is a stable machine-readable code; `detail` stays path-free."""

    def __init__(self, kind: str, detail: str):
        super().__init__(detail)
        self.kind = kind
        self.detail = detail
