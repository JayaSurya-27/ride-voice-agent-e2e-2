import pytest
from uber_voice_agent.agent import load_caller_context
from uber_voice_agent.prompt import build_instructions
from uber_voice_agent.state import BookingState


class FakeClient:
    def __init__(self, harness_mode: bool = False) -> None:
        self.harness_mode = harness_mode
        self.calls: list[str] = []

    async def call(self, endpoint: str, **_: object) -> dict:
        self.calls.append(endpoint)
        return {
            "lookup_rider_by_phone": {
                "rider_id": "rdr_dana",
                "first_name": "Dana",
                "status": "active",
                "default_market": "US-SF",
            },
            "get_saved_places": {"places": [{"label": "home"}, {"label": "work"}]},
            "get_payment_methods": {
                "methods": [{"brand": "Visa", "last4": "4242", "is_default": True}],
                "uber_cash_balance": 5,
            },
        }[endpoint]


@pytest.mark.asyncio
async def test_caller_context_shows_saved_places_and_default_payment() -> None:
    state = BookingState(caller_ani="+14155550101", session_id="room-1")
    context = await load_caller_context(FakeClient(), state)
    prompt = build_instructions(context)
    assert "Saved places: home, work" in prompt
    assert "Default payment: Visa ending 4242" in prompt
    assert "Uber Cash: 5.00" in prompt


@pytest.mark.asyncio
async def test_harness_mode_hydrates_identity_only() -> None:
    client = FakeClient(harness_mode=True)
    state = BookingState(caller_ani="+14155550101", session_id="room-1")
    context = await load_caller_context(client, state)
    assert client.calls == ["lookup_rider_by_phone"]
    assert "saved_places_summary" not in context
