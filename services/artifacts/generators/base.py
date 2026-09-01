from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional
from services.artifacts.models import GeneratedArtifactRecord


class BaseArtifactGenerator(ABC):
    """Abstract sovereign business deliverable generator."""

    @property
    @abstractmethod
    def artifact_type(self) -> str:
        pass

    @abstractmethod
    async def generate(
        self,
        data: Any,
        output_dir: Path,
        task_id: Optional[str] = None,
    ) -> GeneratedArtifactRecord:
        """Generate a real on-disk artifact deliverable and return verified metadata."""
        pass
