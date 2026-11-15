
import pytest
from event_ticket_tier import process_ticket_manifest, monitor_gate_flow


# -------------------------------
# TICKET MANIFEST TEST CASES
# -------------------------------

def test_invalid_manifests():
    with pytest.raises(ValueError):
        process_ticket_manifest("invalid", 0.1)


def test_negative_tax_rate():
    with pytest.raises(ValueError):
        process_ticket_manifest([], -0.1)


def test_empty_manifest_list():
    result = process_ticket_manifest([], 0.1)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_unconfirmed_manifest():
    manifests = [{"is_confirmed": False, "tier": "vip",
                  "orders": [{"qty": 2}]}]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["status"] == "ZERO_SALES"


@pytest.mark.parametrize("tier,qty,expected", [
    ("vip", 1, 165.0),
    ("premium", 2, 198.0),
    ("general", 2, 99.0),
])
def test_ticket_tiers(tier, qty, expected):
    manifests = [{
        "is_confirmed": True,
        "tier": tier,
        "orders": [{"qty": qty}]
    }]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["total_revenue"] == expected
    assert result["status"] == "COMPLETED"


def test_invalid_tier():
    manifests = [{
        "is_confirmed": True,
        "tier": "student",
        "orders": [{"qty": 2}]
    }]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["status"] == "ZERO_SALES"


def test_earlybird_promotion():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "orders": [{"qty": 1, "promo": "EARLYBIRD"}]
    }]
    result = process_ticket_manifest(manifests, 0.0)
    assert result["total_revenue"] == 36.0


def test_bulk_order_discount():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "orders": [{"qty": 5}]
    }]
    result = process_ticket_manifest(manifests, 0.0)
    assert result["total_revenue"] == 205.0


def test_invalid_order_quantities():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "orders": [{"qty": 0}, {"qty": -2}]
    }]
    result = process_ticket_manifest(manifests, 0.0)
    assert result["status"] == "ZERO_SALES"


def test_fraud_in_non_vip_order():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "orders": [
            {"qty": 1, "promo": "FRAUD_RISK"},
            {"qty": 1, "promo": ""}
        ]
    }]
    result = process_ticket_manifest(manifests, 0.0)
    assert result["total_revenue"] == 90.0


def test_vip_fraud_resets_manifest_total():
    manifests = [{
        "is_confirmed": True,
        "tier": "vip",
        "exclusive_lounge": False,
        "orders": [
            {"qty": 2, "promo": ""},
            {"qty": 1, "promo": "FRAUD_RISK"},
            {"qty": 1, "promo": ""}
        ]
    }]
    result = process_ticket_manifest(manifests, 0.0)
    assert result["total_revenue"] == 0.0
    assert result["status"] == "ZERO_SALES"


def test_exclusive_lounge():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "exclusive_lounge": True,
        "orders": []
    }]
    result = process_ticket_manifest(manifests, 0.0)
    assert result["total_revenue"] == 75.0


def test_audit_rejection():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "orders": [{"qty": 0} for _ in range(5)]
    }]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["status"] == "AUDIT_REJECTED"


# -------------------------------
# TURNSTILE TEST CASES
# -------------------------------

def test_gate_flow_no_data():
    assert monitor_gate_flow([]) == "NO_DATA"


def test_gate_flow_overflow():
    assert monitor_gate_flow([[55, 60]]) == "OVERFLOW"


def test_gate_flow_normal():
    assert monitor_gate_flow([[20, 30, 40]]) == "FLOW_NORMAL"
