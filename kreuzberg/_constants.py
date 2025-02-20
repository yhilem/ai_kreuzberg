from __future__ import annotations

from multiprocessing import cpu_count
from typing import Final

DEFAULT_MAX_PROCESSES: Final[int] = cpu_count()
MINIMAL_SUPPORTED_TESSERACT_VERSION: Final[int] = 5
MINIMAL_SUPPORTED_PANDOC_VERSION: Final[int] = 2
