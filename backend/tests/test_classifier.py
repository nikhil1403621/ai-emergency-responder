import pytest
from app.services.classifier import classify_incident


def test_classify_cardiac_emergency():
    text = "Elderly person collapsed, unconscious, possible heart attack with no breathing"
    result = classify_incident(text)
    assert result["suggested_category"] == "medical_emergency"
    assert result["suggested_urgency"] == "critical"
    assert result["confidence"] >= 0.70
    assert result["recommended_unit_type"] == "ambulance"
    assert "heart attack" in result["matched_keywords"] or "unconscious" in result["matched_keywords"]


def test_classify_structure_fire():
    text = "Warehouse building fire, heavy flames and explosion seen on commercial avenue"
    result = classify_incident(text)
    assert result["suggested_category"] == "fire"
    assert result["suggested_urgency"] in ["critical", "high"]
    assert result["recommended_unit_type"] == "fire_engine"
    assert result["requires_review"] is True


def test_classify_highway_collision():
    text = "Three car collision on the expressway with highway wreck blocking two lanes"
    result = classify_incident(text)
    assert result["suggested_category"] == "road_accident"
    assert result["suggested_urgency"] in ["medium", "high"]
    assert "collision" in result["matched_keywords"] or "crash" in result["matched_keywords"]


def test_classify_ambiguous_incident():
    text = "Car crash with burning engine and bleeding injured driver trapped inside"
    result = classify_incident(text)
    # Triggers road accident, fire, and medical emergency
    assert result["requires_review"] is True
    assert result["uncertainty"] >= 0.30
    assert "Multi-domain" in result["reasoning"] or len(result["matched_keywords"]) >= 3


def test_classify_generic_or_unknown():
    text = "Something unusual is happening over behind the library building"
    result = classify_incident(text)
    assert result["suggested_category"] == "other_uncertain"
    assert result["confidence"] <= 0.35
    assert result["requires_review"] is True
