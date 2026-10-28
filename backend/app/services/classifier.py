import re
from typing import Dict, Any, List


CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "medical_emergency": [
        "cardiac", "heart attack", "unconscious", "bleeding", "seizure", "stroke",
        "overdose", "choking", "injury", "injured", "breathing", "ambulance", "cpr",
        "collapsed", "fracture", "blood", "fainted", "head trauma", "burns"
    ],
    "fire": [
        "fire", "smoke", "explosion", "exploding", "burning", "flames", "blaze",
        "wildfire", "gas leak", "hazardous fumes", "chemical spill", "furnace"
    ],
    "road_accident": [
        "crash", "collision", "car accident", "rollover", "vehicle", "pedestrian hit",
        "overturned", "highway wreck", "traffic accident", "multi-car", "hit and run", "truck crash"
    ],
    "crime_security": [
        "robbery", "shooting", "assault", "gun", "gunshot", "weapon", "theft",
        "burglary", "stabbing", "hostage", "active shooter", "violence", "intruder", "knife", "mugging"
    ],
    "natural_disaster": [
        "flood", "flooding", "earthquake", "tornado", "hurricane", "landslide",
        "storm surge", "cyclone", "tsunami", "tremor", "severe storm"
    ],
    "infrastructure_hazard": [
        "power line down", "downed wire", "bridge collapse", "water main burst",
        "gas line rupture", "sinkhole", "structural failure", "blackout", "building collapse"
    ]
}

URGENCY_KEYWORDS: Dict[str, List[str]] = {
    "critical": [
        "unconscious", "not breathing", "cardiac arrest", "active shooter", "trapped",
        "severe bleeding", "massive explosion", "major fire", "fatal", "dying", "suffocating",
        "explosion", "exploding", "blaze"
    ],
    "high": [
        "injury", "injured", "collision", "broken bones", "spreading", "robbery in progress",
        "armed", "violent", "heavy smoke", "gas leak", "head injury", "stabbing", "flames", "burning", "crash"
    ],
    "medium": [
        "minor accident", "property damage", "smoke seen", "hazard", "suspicious",
        "theft", "downed tree", "blocked road", "water leak", "fire"
    ],
    "low": [
        "noise", "parked vehicle", "minor dispute", "inspection", "non-emergency",
        "information", "past incident"
    ]
}

CATEGORY_TO_UNIT_TYPE: Dict[str, str] = {
    "medical_emergency": "ambulance",
    "fire": "fire_engine",
    "road_accident": "ambulance",
    "crime_security": "patrol_car",
    "natural_disaster": "rescue_team",
    "infrastructure_hazard": "utility_truck",
    "other_uncertain": "patrol_car"
}


def classify_incident(description: str) -> Dict[str, Any]:
    text = description.lower()
    
    # 1. Match categories
    category_scores: Dict[str, int] = {}
    matched_by_cat: Dict[str, List[str]] = {}

    for cat, keywords in CATEGORY_KEYWORDS.items():
        matched = []
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                matched.append(kw)
        if matched:
            category_scores[cat] = len(matched)
            matched_by_cat[cat] = matched

    # 2. Determine urgency
    urgency_scores: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    urgency_matched: List[str] = []

    for urg, keywords in URGENCY_KEYWORDS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                urgency_scores[urg] += 1
                urgency_matched.append(kw)

    if urgency_scores["critical"] > 0:
        suggested_urgency = "critical"
    elif urgency_scores["high"] > 0:
        suggested_urgency = "high"
    elif urgency_scores["medium"] > 0:
        suggested_urgency = "medium"
    elif urgency_scores["low"] > 0:
        suggested_urgency = "low"
    else:
        suggested_urgency = "medium"

    # 3. Analyze ambiguity and confidence
    if not category_scores:
        suggested_category = "other_uncertain"
        confidence = 0.25
        uncertainty = 0.75
        requires_review = True
        reasoning = "No recognized emergency keywords matched. Human operator review strongly required."
        matched_keywords = []
    else:
        # Sort by score descending
        sorted_cats = sorted(category_scores.items(), key=lambda item: item[1], reverse=True)
        top_cat, top_score = sorted_cats[0]
        all_matched = [kw for cat in matched_by_cat for kw in matched_by_cat[cat]]

        num_matched_domains = len(sorted_cats)
        base_confidence = min(0.90, 0.60 + (top_score * 0.08))

        # Multi-domain ambiguity penalty
        if num_matched_domains > 1:
            domain_penalty = 0.12 * (num_matched_domains - 1)
            confidence = max(0.40, round(base_confidence - domain_penalty, 2))
            uncertainty = round(1.0 - confidence, 2)
            requires_review = True
            other_domains = [f"{c} ({s})" for c, s in sorted_cats[1:]]
            reasoning = (
                f"Multi-domain incident detected: primary '{top_cat}' ({top_score} match) "
                f"with overlapping indicators in {', '.join(other_domains)}. "
                f"Uncertainty elevated ({uncertainty}). Human dispatcher review required."
            )
        else:
            confidence = round(base_confidence, 2)
            uncertainty = round(1.0 - confidence, 2)
            requires_review = (uncertainty >= 0.35) or (suggested_urgency in ["critical", "high"])
            reasoning = (
                f"Categorized as '{top_cat}' based on {top_score} keyword matches: "
                f"{', '.join(matched_by_cat[top_cat])}. Urgency evaluated as '{suggested_urgency}'."
            )

        suggested_category = top_cat
        matched_keywords = all_matched

    recommended_unit_type = CATEGORY_TO_UNIT_TYPE.get(suggested_category, "patrol_car")

    return {
        "model_version": "v1.0-rule-baseline",
        "suggested_category": suggested_category,
        "suggested_urgency": suggested_urgency,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "requires_review": requires_review,
        "reasoning": reasoning,
        "matched_keywords": matched_keywords,
        "recommended_unit_type": recommended_unit_type
    }
