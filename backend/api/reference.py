"""Read-only endpoints that expose the static SOC reference data.

Powers the in-app Knowledge Base page (Severity Dictionary, Threat Dictionary,
STRIDE Analysis, Risk Matrix). Requires an authenticated user so the same
session-scope rules apply as for chat - no need for admin role.
"""

from fastapi import APIRouter, Depends, HTTPException

from auth.middleware import get_current_user
from database.models import User
from data.threat_catalog import all_threats, get_threat
from data.severity_dictionary import SEVERITY_LEVELS, get_level
from data.stride_analysis import STRIDE_ANALYSIS, RISK_MATRIX, get_category
from data.mitre_techniques import all_techniques, get_technique

router = APIRouter()


@router.get("/severity")
async def list_severity(user: User = Depends(get_current_user)) -> list[dict]:
    return SEVERITY_LEVELS


@router.get("/severity/{level}")
async def get_severity(level: str, user: User = Depends(get_current_user)) -> dict:
    entry = get_level(level)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Unknown severity level: {level}")
    return entry


@router.get("/threats")
async def list_threats(user: User = Depends(get_current_user)) -> list[dict]:
    return all_threats()


@router.get("/threats/{threat_id}")
async def get_threat_by_id(threat_id: str, user: User = Depends(get_current_user)) -> dict:
    entry = get_threat(threat_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Unknown threat id: {threat_id}")
    return entry


@router.get("/stride")
async def list_stride(user: User = Depends(get_current_user)) -> list[dict]:
    return STRIDE_ANALYSIS


@router.get("/stride/{category}")
async def get_stride(category: str, user: User = Depends(get_current_user)) -> dict:
    entry = get_category(category)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Unknown STRIDE category: {category}")
    return entry


@router.get("/risk-matrix")
async def risk_matrix(user: User = Depends(get_current_user)) -> list[dict]:
    return RISK_MATRIX


@router.get("/mitre")
async def list_mitre(user: User = Depends(get_current_user)) -> list[dict]:
    """Return every curated MITRE ATT&CK technique entry."""
    return all_techniques()


@router.get("/mitre/{technique_id}")
async def get_mitre(technique_id: str, user: User = Depends(get_current_user)) -> dict:
    """Return one MITRE technique by ID.

    Unknown IDs return 404 with a hint to attack.mitre.org so the UI can show
    a "not in local dictionary - view at mitre.org" fallback card.
    """
    entry = get_technique(technique_id)
    if not entry:
        canonical = technique_id.strip().upper()
        if "." in canonical:
            parent, sub = canonical.split(".", 1)
            url = f"https://attack.mitre.org/techniques/{parent}/{sub}/"
        else:
            url = f"https://attack.mitre.org/techniques/{canonical}/"
        raise HTTPException(
            status_code=404,
            detail={
                "id": canonical,
                "reason": "Technique not in local dictionary.",
                "mitre_url": url,
            },
        )
    return entry
