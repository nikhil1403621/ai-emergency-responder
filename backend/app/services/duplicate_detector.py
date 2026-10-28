import math
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in km."""
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def tokenize(text: str) -> set:
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    stop_words = {"the", "and", "near", "with", "from", "that", "this", "there", "some", "have", "been"}
    return {w for w in words if w not in stop_words}


def text_jaccard_similarity(text1: str, text2: str) -> float:
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return round(len(intersection) / len(union), 2)


def find_duplicate_candidates(
    new_description: str,
    new_lat: Optional[float],
    new_lon: Optional[float],
    existing_incidents: List[Dict[str, Any]],
    similarity_threshold: float = 0.35,
    max_distance_km: float = 3.0
) -> List[Dict[str, Any]]:
    candidates = []

    for incident in existing_incidents:
        text_sim = text_jaccard_similarity(new_description, incident["description"])
        dist_km = None

        if new_lat is not None and new_lon is not None and incident["latitude"] is not None and incident["longitude"] is not None:
            dist_km = haversine_distance_km(new_lat, new_lon, incident["latitude"], incident["longitude"])

        is_candidate = False
        composite_score = text_sim

        # If spatial data exists and nearby
        if dist_km is not None:
            if dist_km <= max_distance_km and text_sim >= 0.25:
                # Proximity boosts duplicate suspicion
                proximity_factor = max(0.0, 1.0 - (dist_km / max_distance_km))
                composite_score = round(0.5 * text_sim + 0.5 * proximity_factor, 2)
                if composite_score >= similarity_threshold:
                    is_candidate = True
        else:
            # No coordinates; rely solely on text
            if text_sim >= 0.45:
                is_candidate = True

        if is_candidate:
            candidates.append({
                "incident_id": incident["id"],
                "description": incident["description"],
                "similarity_score": composite_score,
                "distance_km": dist_km,
                "created_at": incident["created_at"],
                "status": incident["status"]
            })

    # Sort descending by similarity score
    candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
    return candidates
