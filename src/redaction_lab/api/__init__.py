"""Local, loopback-only HTTP API for Redaction Lab."""

from redaction_lab.api.app import LocalApi, create_app

__all__ = ["LocalApi", "create_app"]
