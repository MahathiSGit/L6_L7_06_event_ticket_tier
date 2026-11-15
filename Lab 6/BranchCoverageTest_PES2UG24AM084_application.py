
import pytest
from event_ticket_tier import process_ticket_manifest, monitor_gate_flow


# ==========================================
# 1. INPUT VALIDATION BRANCHES
# ==========================================

def test_invalid_manifest_type():
    with pytest.raises(ValueError):
        process_ticket_manifest("invalid", 0.1)


def test_negative_tax():
    with pytest.raises(ValueError):
        process_ticket_manifest([], -0.1)


def test_valid_empty_manifest_list():
    result = process_ticket_manifest([], 0.1)
    assert result["status"] == "ZERO_SALES"


# ==========================================
# 2. MANIFEST CONFIRMATION BRANCHES
# ==========================================

def test_confirmed_manifest():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "orders": [{"qty": 1}]
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["total_revenue"] == 45.0


def test_unconfirmed_manifest():
    manifests = [{
        "is_confirmed": False,
        "tier": "vip",
        "orders": [{"qty": 1}]
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["status"] == "ZERO_SALES"


# ==========================================
# 3. SEATING TIER BRANCHES
# ==========================================

@pytest.mark.parametrize("tier, expected", [
    ("vip", 150.0),
    ("premium", 90.0),
    ("general", 45.0),
])
def test_valid_seating_tiers(tier, expected):
    manifests = [{
        "is_confirmed": True,
        "tier": tier,
        "orders": [{"qty": 1}]
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["total_revenue"] == expected


def test_invalid_seating_tier():
    manifests = [{
        "is_confirmed": True,
        "tier": "student",
        "orders": [{"qty": 1}]
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["status"] == "ZERO_SALES"


# ==========================================
# 4. ORDER QUANTITY BRANCHES
# ==========================================

@pytest.mark.parametrize("qty", [0, -1])
def test_invalid_quantities(qty):
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "orders": [{"qty": qty}]
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["status"] == "ZERO_SALES"


def test_valid_quantity():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "orders": [{"qty": 2}]
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["total_revenue"] == 90.0


# ==========================================
# 5. PROMOTIONAL CODE BRANCHES
# ==========================================

def test_fraud_risk_vip():
    manifests = [{
        "is_confirmed": True,
        "tier": "vip",
        "orders": [
            {"qty": 1, "promo": "FRAUD_RISK"}
        ]
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["status"] == "ZERO_SALES"


def test_fraud_risk_non_vip():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "orders": [
            {"qty": 1, "promo": "FRAUD_RISK"}
        ]
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["total_revenue"] == 45.0


def test_earlybird_promotion():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "orders": [{"qty": 1, "promo": "EARLYBIRD"}]
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["total_revenue"] == 36.0


def test_regular_order_below_five():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "orders": [{"qty": 4, "promo": ""}]
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["total_revenue"] == 180.0


def test_regular_order_at_least_five():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "orders": [{"qty": 5, "promo": ""}]
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["total_revenue"] == 205.0


# ==========================================
# 6. VIP FRAUD AND LOUNGE BRANCHES
# ==========================================

def test_vip_fraud_breaks_order_loop():
    manifests = [{
        "is_confirmed": True,
        "tier": "vip",
        "exclusive_lounge": False,
        "orders": [
            {"qty": 1, "promo": ""},
            {"qty": 1, "promo": "FRAUD_RISK"},
            {"qty": 1, "promo": ""}
        ]
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["total_revenue"] == 0.0


def test_lounge_enabled():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "exclusive_lounge": True,
        "orders": []
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["total_revenue"] == 75.0


def test_lounge_disabled():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "exclusive_lounge": False,
        "orders": []
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["total_revenue"] == 0.0


# ==========================================
# 7. AUDIT AND SALES STATUS BRANCHES
# ==========================================

def test_audit_rejected():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "orders": [{"qty": 0} for _ in range(5)]
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["status"] == "AUDIT_REJECTED"


def test_audit_not_rejected():
    manifests = [{
        "is_confirmed": True,
        "tier": "general",
        "orders": [{"qty": 0} for _ in range(4)]
    }]
    result = process_ticket_manifest(manifests, 0)
    assert result["status"] == "ZERO_SALES"


def test_completed_status():
    manifests = [{
        "is_confirmed": True,
        "tier": "premium",
        "orders": [{"qty": 2}]
    }]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["status"] == "COMPLETED"
    assert result["total_revenue"] == 198.0


# ==========================================
# 8. TURNSTILE FLOW BRANCHES
# ==========================================

def test_no_turnstile_data():
    assert monitor_gate_flow([]) == "NO_DATA"


def test_normal_turnstile_flow():
    assert monitor_gate_flow([[20, 30, 40]]) == "FLOW_NORMAL"


def test_single_high_rate():
    assert monitor_gate_flow([[60]]) == "FLOW_NORMAL"


def test_two_consecutive_high_rates():
    assert monitor_gate_flow([[60, 70]]) == "OVERFLOW"


def test_congestion_streak_reset():
    assert monitor_gate_flow([[60, 40, 65]]) == "FLOW_NORMAL"


def test_overflow_after_streak_reset():
    assert monitor_gate_flow([[60, 40, 65, 70]]) == "OVERFLOW"


def test_multiple_turnstile_streams():
    assert monitor_gate_flow([[60], [30, 40]]) == "FLOW_NORMAL"
