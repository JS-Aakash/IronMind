import io
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union
from packages.shared.utils.helpers import generate_uuid
from services.document_intelligence.models import BoundingBox, ImageRegion

logger = logging.getLogger(__name__)


class ImageExtractor:
    """Extracts visual properties, dimensions, and image regions from images and scanned documents."""

    def extract_image_region(
        self,
        image_input: Union[bytes, Path, str],
        page_number: int = 1,
        filename: Optional[str] = None,
    ) -> ImageRegion:
        width = 800
        height = 600
        image_type = "diagram"

        fn = filename.lower() if filename else (str(image_input).lower() if isinstance(image_input, (Path, str)) else "")
        if "pid" in fn or "p&id" in fn or "drawing" in fn or "schematic" in fn:
            image_type = "pid"
        elif "chart" in fn or "curve" in fn:
            image_type = "chart"
        elif "photo" in fn or "site" in fn:
            image_type = "photo"

        try:
            from PIL import Image
            if isinstance(image_input, (Path, str)):
                with Image.open(image_input) as img:
                    width, height = img.size
            else:
                with Image.open(io.BytesIO(image_input)) as img:
                    width, height = img.size
        except Exception as e:
            logger.debug("PIL metadata read skipped or unavailable: %s", str(e))

        return ImageRegion(
            image_id=generate_uuid("IMG"),
            page_number=page_number,
            image_type=image_type,
            bbox=BoundingBox(x0=0, y0=0, x1=float(width), y1=float(height)),
            description=f"Extracted {image_type.upper()} image region ({width}x{height})",
            width=width,
            height=height,
        )
