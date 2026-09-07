from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ApprovalNoteData(BaseModel):
    subject: str = Field(description="Subject of the approval note")
    equipment_tag: str = Field(default="P-101", description="Equipment Tag (e.g. P-101)")
    equipment_name: str = Field(default="Centrifugal Slurry Pump (API 610 BB2)")
    operating_unit: str = Field(default="CDU-1 Crude Distillation Unit")
    inspection_date: str = Field(default="28-AUG-2026")
    inspection_summary: str = Field(default="Routine dynamic vibration monitoring and mechanical seal integrity inspection.")
    measured_parameters: Dict[str, Any] = Field(
        default_factory=lambda: {
            "Overall Vibration RMS (mm/s)": 4.8,
            "ISO 10816-3 Threshold (mm/s)": 4.5,
            "Bearing Temperature (°C)": 78.5,
            "Discharge Pressure (bar)": 12.4,
            "Suction Pressure (bar)": 2.1,
        }
    )
    findings: List[str] = Field(
        default_factory=lambda: [
            "Drive-end bearing overall vibration measured at 4.8 mm/s RMS, exceeding ISO 10816 Zone B limit (4.5 mm/s).",
            "Minor fluid weeping observed on mechanical seal primary face.",
            "High-frequency FFT spectrum indicates early-stage rolling element spalling on outer raceway.",
        ]
    )
    recommendations: List[str] = Field(
        default_factory=lambda: [
            "Issue immediate priority work order for bearing cartridge overhaul.",
            "Inspect and replace mechanical seal with API Plan 53B pressurized barrier fluid verification.",
            "Perform dynamic balancing and laser shaft alignment prior to restarting Unit 04.",
        ]
    )
    sop_references: List[str] = Field(
        default_factory=lambda: [
            "MRPL SOP-MECH-4.2 (Vibration Safety Thresholds)",
            "API Standard 610 (Centrifugal Pumps for Petroleum Industries)",
            "ISO 10816-3 (Evaluation of Machine Vibration on Non-Rotating Parts)",
        ]
    )
    justification: str = Field(
        default="Operating the pump above 4.5 mm/s presents critical risk of catastrophic bearing seizure, uncontained seal breach, and unplanned refinery unit shutdown."
    )
    cost_estimate_inr: Optional[str] = Field(default="₹ 3,45,000 (Overhaul + Seal Assembly)")
    signatories: Dict[str, str] = Field(
        default_factory=lambda: {
            "Prepared By": "Aakash (Mechanical Maintenance Engineer)",
            "Verified By": "Lead Reliability Engineer (MRPL Division)",
            "Approved By": "Chief General Manager (Technical Services)",
        }
    )
    task_id: Optional[str] = None
    source_documents: List[str] = Field(default_factory=lambda: ["inspection_report.pdf", "MRPL_SOP_P101.pdf"])
    models_used: List[str] = Field(default_factory=lambda: ["qwen2.5vl:7b", "qwen3:8b"])


class SpreadsheetData(BaseModel):
    title: str = Field(default="Equipment Inspection Log")
    sheets: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "Vibration_Readings": {
                "headers": ["Equipment Tag", "Speed (RPM)", "Measured RMS (mm/s)", "Limit (mm/s)", "Status"],
                "rows": [
                    ["P-101A", 1480, 4.8, 4.5, "ALERT"],
                    ["P-101B", 1480, 2.3, 4.5, "NORMAL"],
                    ["P-102A", 2950, 1.8, 4.5, "NORMAL"],
                    ["P-102B", 2950, 2.1, 4.5, "NORMAL"],
                ],
            }
        }
    )
    task_id: Optional[str] = None
    source_documents: List[str] = Field(default_factory=list)
    models_used: List[str] = Field(default_factory=lambda: ["qwen2.5-coder:7b"])


class PresentationData(BaseModel):
    title: str = Field(default="MRPL Equipment Reliability Review")
    subtitle: Optional[str] = Field(default="Unit 04 Slurry Pump Mechanical Integrity Assessment")
    slides: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {
                "title": "Executive Summary",
                "bullet_points": [
                    "Equipment Tag: P-101 Centrifugal Slurry Pump.",
                    "Measured drive-end vibration: 4.8 mm/s (ISO limit 4.5 mm/s).",
                    "Mechanical seal primary face weeping detected.",
                    "Recommendation: Priority overhaul within 72 hours.",
                ],
            },
            {
                "title": "Technical Findings & FFT Spectrum",
                "bullet_points": [
                    "Bearing temperature elevated at 78.5°C.",
                    "Harmonic peaks at 2X and 3X running speed confirm bearing outer race wear.",
                    "Seal flush pressure stable at 1.8 bar.",
                ],
            },
            {
                "title": "Action Plan & Next Steps",
                "bullet_points": [
                    "Shift load to standby unit P-101B immediately.",
                    "Issue work order for bearing cartridge replacement.",
                    "Re-align with laser optical kit to < 0.05 mm tolerance.",
                ],
            },
        ]
    )
    task_id: Optional[str] = None
    source_documents: List[str] = Field(default_factory=list)
    models_used: List[str] = Field(default_factory=lambda: ["qwen3:8b"])


class PdfReportData(BaseModel):
    title: str = Field(default="MRPL Industrial Engineering Summary")
    equipment_tag: str = Field(default="P-101")
    paragraphs: List[str] = Field(
        default_factory=lambda: [
            "This technical evaluation summary document has been generated autonomously within the on-premise air-gapped IronMind Sovereign Workbench.",
            "All quantitative measurements and vibration parameters were extracted using local open-weight vision models (Qwen2.5-VL) and verified against MRPL SOPs.",
            "Zero telemetry or engineering data was transmitted outside refinery premises.",
        ]
    )
    table_headers: Optional[List[str]] = Field(default_factory=lambda: ["Tag", "Parameter", "Value", "Status"])
    table_rows: Optional[List[List[str]]] = Field(
        default_factory=lambda: [
            ["P-101", "Vibration RMS", "4.8 mm/s", "EXCEEDED"],
            ["P-101", "Bearing Temp", "78.5 °C", "WARNING"],
            ["P-101", "Discharge Head", "45.0 m", "NORMAL"],
        ]
    )
    task_id: Optional[str] = None
    source_documents: List[str] = Field(default_factory=list)
    models_used: List[str] = Field(default_factory=lambda: ["qwen3:8b"])


class GeneratedArtifactRecord(BaseModel):
    artifact_id: str
    task_id: Optional[str] = None
    filename: str
    type: str  # "docx" | "xlsx" | "pptx" | "pdf" | "python" | "text"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    source_documents: List[str] = Field(default_factory=list)
    models_used: List[str] = Field(default_factory=list)
    verification_status: str = "verified"
    verified: bool = True
    sha256_hash: str
    size_bytes: int
    file_path: str
    download_url: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
