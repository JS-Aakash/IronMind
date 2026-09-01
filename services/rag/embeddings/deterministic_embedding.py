import hashlib
import math
import re
from typing import List
from services.rag.embeddings.base import BaseEmbeddingProvider


class DeterministicLocalEmbeddingProvider(BaseEmbeddingProvider):
    """High-speed sovereign on-premise dense embedding provider (384-dimensional) with semantic keyword resonance."""

    DIMENSION = 384

    # Industrial semantic concept anchors
    CONCEPT_ANCHORS = {
        "vibration": 10, "bearing": 25, "pump": 40, "slurry": 55, "pressure": 70,
        "temperature": 85, "seal": 100, "maintenance": 115, "overhaul": 130,
        "sop": 145, "threshold": 160, "api610": 175, "api510": 190, "cavitation": 205,
        "efficiency": 220, "flow": 235, "head": 250, "hydraulic": 265, "inspection": 280,
        "distillation": 295, "cdu": 310, "pid": 325, "diagram": 340, "safety": 355,
        "valve": 120, "flaring": 210, "rate": 215, "limit": 165,
    }

    @property
    def provider_name(self) -> str:
        return "DeterministicLocalDenseEmbedding (384d)"

    @property
    def dimension(self) -> int:
        return self.DIMENSION

    def embed_text_sync(self, text: str) -> List[float]:
        vec = [0.0] * self.DIMENSION
        clean_text = text.lower()
        tokens = re.findall(r"\b[a-z0-9_]+\b", clean_text)

        if not tokens:
            return [1.0 / math.sqrt(self.DIMENSION)] * self.DIMENSION

        # 1. Base character n-gram and token hash dispersion
        for token in tokens:
            thash = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = thash % self.DIMENSION
            weight = 1.0 + (len(token) * 0.1)
            vec[idx] += weight

            # 2. Semantic concept anchor resonance
            for concept, anchor_idx in self.CONCEPT_ANCHORS.items():
                if concept in token or token in concept:
                    for offset in range(-3, 4):
                        pos = (anchor_idx + offset) % self.DIMENSION
                        vec[pos] += 3.5 / (abs(offset) + 1.0)

        # 3. L2 Normalize vector
        magnitude = math.sqrt(sum(v * v for v in vec))
        if magnitude > 0:
            vec = [round(v / magnitude, 6) for v in vec]
        else:
            vec = [1.0 / math.sqrt(self.DIMENSION)] * self.DIMENSION

        return vec

    async def embed_text(self, text: str) -> List[float]:
        return self.embed_text_sync(text)
