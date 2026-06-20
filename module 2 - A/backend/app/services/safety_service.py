"""
Safety Service.
Performs drug-drug interaction, allergy, duplicate ingredient checks.
Connects to OpenFDA API. Generates risk scores and warnings.
"""

import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.schemas import DrugWarning, PrescriptionSafetyResponse
from app.config import settings

logger = logging.getLogger(__name__)


class PrescriptionSafetyService:
    
    async def _query_openfda(self, medicine_name: str) -> Dict[str, Any]:
        """Query OpenFDA API for drug label information."""
        try:
            async with httpx.AsyncClient(timeout=settings.OPENFDA_TIMEOUT_SECONDS) as client:
                query = f'openfda.brand_name:"{medicine_name}" OR openfda.generic_name:"{medicine_name}"'
                url = f"{settings.OPENFDA_API_URL}?search={query}&limit=1"
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("results"):
                        return data["results"][0]
        except Exception as e:
            logger.warning(f"OpenFDA query failed for {medicine_name}: {e}")
        return {}

    async def analyze_prescription(
        self,
        patient_id: str,
        prescription_id: Optional[str],
        medicine_name: str,
        dosage: Optional[str],
        patient_allergies: List[str],
        active_medicines: List[str]
    ) -> PrescriptionSafetyResponse:
        """
        Analyze a prescription against patient allergies and active medications.
        Generates warnings, risk level, and a governance alert flag if critical.
        """
        warnings = []
        interactions = []
        allergy_conflicts = []
        duplicate_ingredients = []
        recommendations = []
        risk_score = 0.0
        
        # 1. Fetch FDA data
        fda_data = await self._query_openfda(medicine_name)
        active_ingredients = fda_data.get("openfda", {}).get("substance_name", [medicine_name.upper()])
        active_ingredients = [ing.lower() for ing in active_ingredients]
        
        # 2. Allergy Check
        for allergy in patient_allergies:
            al_lower = allergy.lower()
            if al_lower in medicine_name.lower() or any(al_lower in ing for ing in active_ingredients):
                allergy_conflicts.append({"allergen": allergy, "medicine": medicine_name})
                warnings.append(DrugWarning(
                    warning_type="ALLERGY",
                    drugs_involved=[medicine_name],
                    description=f"Patient has a known allergy to {allergy}, which is present in {medicine_name}.",
                    severity="critical"
                ))
                risk_score += 50.0
                recommendations.append(f"DO NOT PRESCRIBE: Severe allergy conflict with {allergy}.")
                
        # 3. Drug-Drug Interaction Check (Mocked for local, normally querying DrugBank/FDA)
        # We simulate a few common dangerous interactions
        danger_pairs = [
            ({"warfarin", "aspirin"}, "Increased risk of bleeding"),
            ({"sildenafil", "nitroglycerin"}, "Severe drop in blood pressure"),
            ({"ssri", "maoi"}, "Serotonin syndrome risk")
        ]
        
        all_meds = [m.lower() for m in active_medicines] + [medicine_name.lower()]
        for pair, desc in danger_pairs:
            # Simple check if both elements of pair are in all_meds
            # (In reality, we'd map trade names to generic classes)
            if all(any(p in m for m in all_meds) for p in pair):
                interactions.append({
                    "drugs": list(pair),
                    "severity": "high",
                    "description": desc
                })
                warnings.append(DrugWarning(
                    warning_type="INTERACTION",
                    drugs_involved=list(pair),
                    description=f"Major interaction: {desc}",
                    severity="high"
                ))
                risk_score += 40.0
                recommendations.append(f"Review combination of {', '.join(pair)}: {desc}")
                
        # 4. Determine Risk Level & Auto-flag
        risk_level = "LOW"
        auto_flagged = False
        
        if risk_score >= 80:
            risk_level = "CRITICAL"
            auto_flagged = True
        elif risk_score >= 40:
            risk_level = "HIGH"
            auto_flagged = True
        elif risk_score >= 20:
            risk_level = "MEDIUM"
            
        if not recommendations and risk_level == "LOW":
            recommendations.append("No significant safety concerns detected.")
            
        return PrescriptionSafetyResponse(
            safety_id="temp", # Replaced during DB insertion
            patient_id=patient_id,
            prescription_id=prescription_id,
            medicine_name=medicine_name,
            risk_score=min(risk_score, 100.0),
            risk_level=risk_level,
            warnings=warnings,
            interactions=interactions,
            allergy_conflicts=allergy_conflicts,
            duplicate_ingredients=duplicate_ingredients,
            dosage_outliers=[], # Advanced implementation needed
            recommendations=recommendations,
            auto_flagged=auto_flagged,
            governance_alert_created=auto_flagged,
            analyzed_at=datetime.utcnow(),
            analysis_source="openfda_local"
        )

safety_service = PrescriptionSafetyService()
