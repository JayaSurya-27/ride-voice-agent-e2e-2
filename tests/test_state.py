import pytest
from uber_voice_agent.state import BookingState, GuardError


def ready_state() -> BookingState:
    state = BookingState(caller_ani="+14155550101", session_id="room-1")
    state.set_identity(
        {
            "rider_id": "rdr_dana",
            "first_name": "Dana",
            "status": "active",
            "default_market": "US-SF",
            "accessibility_needs": [],
        }
    )
    state.remember_geocode(
        "pickup",
        [{"place_id": "pickup", "formatted_address": "One Main Street"}],
    )
    state.confirm_address("pickup", "pickup")
    state.remember_geocode(
        "dropoff",
        [{"place_id": "dropoff", "formatted_address": "SFO Terminal One"}],
    )
    state.confirm_address("dropoff", "dropoff")
    state.remember_quote(
        {
            "currency": "USD",
            "surge_multiplier": 1.0,
            "options": [
                {
                    "product_id": "uberx",
                    "display_name": "UberX",
                    "fare_low": 18.0,
                    "fare_high": 22.0,
                    "eta_pickup_min": 4,
                    "is_available": True,
                }
            ],
        }
    )
    state.select_product("uberx")
    return state


def test_booking_requires_confirmed_addresses() -> None:
    state = BookingState(caller_ani="+1", session_id="room")
    with pytest.raises(GuardError, match="pickup and destination"):
        state.remember_quote({"options": []})


def test_uber_cash_must_cover_high_quote() -> None:
    state = ready_state()
    state.uber_cash_balance = 21.99
    with pytest.raises(GuardError, match="does not cover"):
        state.select_payment("uber_cash")

    state.uber_cash_balance = 22.00
    state.select_payment("uber_cash")
    assert state.payment_method_selected == "uber_cash"


def test_saved_card_requires_otp() -> None:
    state = ready_state()
    state.payment_methods = [
        {
            "id": "pm_visa",
            "type": "card",
            "is_valid": True,
            "is_expired": False,
        }
    ]
    with pytest.raises(GuardError, match="OTP"):
        state.select_payment("saved_card:pm_visa")

    state.auth_level = "otp_verified"
    state.select_payment("saved_card:pm_visa")
    assert state.payment_method_selected == "saved_card:pm_visa"


def test_expired_saved_card_is_rejected() -> None:
    state = ready_state()
    state.auth_level = "otp_verified"
    state.payment_methods = [
        {"id": "pm_mc", "type": "card", "is_valid": False, "is_expired": True}
    ]
    with pytest.raises(GuardError, match="not valid"):
        state.select_payment("saved_card:pm_mc")


def test_unsupported_payment_methods_are_rejected() -> None:
    state = ready_state()
    state.uber_cash_balance = 100
    for method in ("cash", "pay_link"):
        with pytest.raises(GuardError, match="Unsupported payment method"):
            state.select_payment(method)


def test_destination_change_invalidates_quote_payment_and_consent() -> None:
    state = ready_state()
    state.uber_cash_balance = 100
    state.select_payment("uber_cash")
    token, _ = state.prepare_confirmation()

    state.remember_geocode(
        "dropoff",
        [{"place_id": "new-dropoff", "formatted_address": "Oakland Airport"}],
    )
    state.confirm_address("dropoff", "new-dropoff")

    assert state.selected_product_id is None
    assert state.payment_method_selected is None
    with pytest.raises(GuardError, match="confirmation"):
        state.authorize_booking(token, caller_explicitly_confirmed=True)


def test_confirmation_token_is_exact_and_one_time() -> None:
    state = ready_state()
    state.uber_cash_balance = 100
    state.select_payment("uber_cash")
    token, summary = state.prepare_confirmation()
    assert "UberX" in summary
    assert "18.00 to 22.00 USD" in summary

    with pytest.raises(GuardError, match="explicit yes"):
        state.authorize_booking(token, caller_explicitly_confirmed=False)
    with pytest.raises(GuardError, match="does not match"):
        state.authorize_booking("wrong", caller_explicitly_confirmed=True)

    state.authorize_booking(token, caller_explicitly_confirmed=True)
    with pytest.raises(GuardError, match="confirmation"):
        state.authorize_booking(token, caller_explicitly_confirmed=True)


@pytest.mark.parametrize("status", ["suspended", "payment_hold", "banned"])
def test_blocked_account_cannot_enter_transaction(status: str) -> None:
    state = ready_state()
    state.rider_status = status

    with pytest.raises(GuardError, match="cannot book rides"):
        state.select_product("uberx")


def test_active_account_remains_bookable() -> None:
    state = ready_state()
    state.ensure_bookable()
    assert state.selected_product_id == "uberx"
