"""Bounded OCR interface for the isolated PDF worker."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import BytesIO, StringIO
from math import isfinite
import os
import subprocess
from typing import Protocol

from PIL import Image


TESSERACT_VERSION = "5.5.2"
TESSERACT_LANGUAGE = "eng"
DEFAULT_OCR_TIMEOUT_SECONDS = 20
DEFAULT_MAX_OCR_OUTPUT_BYTES = 4 * 1024 * 1024
MAX_OCR_WORDS = 50_000
MAX_OCR_PIXELS = 8_000_000
_TSV_FIELDS = (
    "level",
    "page_num",
    "block_num",
    "par_num",
    "line_num",
    "word_num",
    "left",
    "top",
    "width",
    "height",
    "conf",
    "text",
)


class OcrFailure(RuntimeError):
    """Sanitized OCR failure that never retains engine output."""


@dataclass(frozen=True)
class OcrWord:
    text: str
    confidence: float
    bbox: tuple[int, int, int, int]
    line_key: tuple[int, int, int]


@dataclass(frozen=True)
class OcrPage:
    width: int
    height: int
    words: tuple[OcrWord, ...]
    engine: str = f"tesseract-{TESSERACT_VERSION}-{TESSERACT_LANGUAGE}"


class OcrEngine(Protocol):
    def recognize(self, image: Image.Image) -> OcrPage: ...


class OcrRunner(Protocol):
    def run(
        self, input_bytes: bytes, *, timeout_seconds: int
    ) -> tuple[int, bytes, bytes]: ...


class SubprocessOcrRunner:
    """Execute the pinned worker-local Tesseract binary without a shell."""

    def __init__(self, executable: str = "/usr/bin/tesseract") -> None:
        self.executable = executable

    def run(
        self, input_bytes: bytes, *, timeout_seconds: int
    ) -> tuple[int, bytes, bytes]:
        completed = subprocess.run(
            (
                self.executable,
                "stdin",
                "stdout",
                "-l",
                TESSERACT_LANGUAGE,
                "--dpi",
                "200",
                "--psm",
                "6",
                "tsv",
            ),
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
            cwd="/",
            env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
        )
        return completed.returncode, completed.stdout, completed.stderr


class TesseractOcrEngine:
    def __init__(
        self,
        *,
        runner: OcrRunner | None = None,
        timeout_seconds: int = DEFAULT_OCR_TIMEOUT_SECONDS,
        max_output_bytes: int = DEFAULT_MAX_OCR_OUTPUT_BYTES,
    ) -> None:
        if not 1 <= timeout_seconds <= 60 or not 1 <= max_output_bytes <= 16 * 1024 * 1024:
            raise ValueError("invalid OCR resource limit")
        self._runner = runner or SubprocessOcrRunner()
        self._timeout_seconds = timeout_seconds
        self._max_output_bytes = max_output_bytes

    @staticmethod
    def _png_bytes(image: Image.Image) -> bytes:
        if (
            isinstance(image.width, bool)
            or isinstance(image.height, bool)
            or image.width < 1
            or image.height < 1
            or image.width * image.height > MAX_OCR_PIXELS
        ):
            raise OcrFailure("OCR image is outside resource limits")
        output = BytesIO()
        try:
            image.convert("RGB").save(output, format="PNG", optimize=False)
        except Exception:
            raise OcrFailure("OCR image encoding failed") from None
        payload = output.getvalue()
        if len(payload) > 32 * 1024 * 1024:
            raise OcrFailure("OCR image is outside resource limits")
        return payload

    @staticmethod
    def _parse_int(row: dict[str, str], field: str) -> int:
        value = int(row[field])
        if isinstance(value, bool):
            raise ValueError
        return value

    def _parse(self, payload: bytes, *, width: int, height: int) -> tuple[OcrWord, ...]:
        if len(payload) > self._max_output_bytes:
            raise OcrFailure("OCR output exceeded its limit")
        try:
            decoded = payload.decode("utf-8", errors="strict")
            reader = csv.DictReader(StringIO(decoded), delimiter="\t")
            if tuple(reader.fieldnames or ()) != _TSV_FIELDS:
                raise ValueError
            words: list[OcrWord] = []
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError
                if self._parse_int(row, "level") != 5:
                    continue
                text = row["text"].strip()
                if not text:
                    continue
                if any(ord(character) < 32 or ord(character) == 127 for character in text):
                    raise ValueError
                confidence = float(row["conf"])
                left = self._parse_int(row, "left")
                top = self._parse_int(row, "top")
                word_width = self._parse_int(row, "width")
                word_height = self._parse_int(row, "height")
                block = self._parse_int(row, "block_num")
                paragraph = self._parse_int(row, "par_num")
                line = self._parse_int(row, "line_num")
                if (
                    not isfinite(confidence)
                    or not 0.0 <= confidence <= 100.0
                    or left < 0
                    or top < 0
                    or word_width < 1
                    or word_height < 1
                    or left + word_width > width
                    or top + word_height > height
                    or block < 1
                    or paragraph < 1
                    or line < 1
                ):
                    raise ValueError
                words.append(
                    OcrWord(
                        text=text,
                        confidence=confidence,
                        bbox=(left, top, left + word_width, top + word_height),
                        line_key=(block, paragraph, line),
                    )
                )
                if len(words) > MAX_OCR_WORDS:
                    raise ValueError
            return tuple(words)
        except (UnicodeDecodeError, csv.Error, KeyError, TypeError, ValueError):
            raise OcrFailure("OCR output was invalid") from None

    def recognize(self, image: Image.Image) -> OcrPage:
        payload = self._png_bytes(image)
        try:
            returncode, stdout, _stderr = self._runner.run(
                payload,
                timeout_seconds=self._timeout_seconds,
            )
        except (OSError, TimeoutError, subprocess.TimeoutExpired):
            raise OcrFailure("OCR execution failed") from None
        if returncode != 0:
            raise OcrFailure("OCR execution failed")
        words = self._parse(stdout, width=image.width, height=image.height)
        return OcrPage(width=image.width, height=image.height, words=words)
