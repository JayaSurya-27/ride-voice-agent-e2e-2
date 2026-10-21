from uber_voice_agent.prompt import build_instructions


def test_prompt_contains_non_negotiable_voice_and_booking_rules() -> None:
    prompt = build_instructions(
        {
            "caller_ani": "+14155550101",
            "rider_id": "rdr_dana",
            "first_name": "Dana",
            "status": "active",
            "default_market": "US-SF",
        }
    )
    for required in (
        "one question at a time",
        "Never invent",
        "Never ask for or accept a full card number",
        "prepare_booking_confirmation",
        "explicit yes",
        "transfer_to_human",
        "how many riders and how many large bags",
    ):
        assert required.lower() in prompt.lower()


def test_prompt_does_not_expose_unknown_saved_data() -> None:
    prompt = build_instructions({"caller_ani": "+19995550123"})
    assert "Account on file: no" in prompt
    assert "Name: unknown" in prompt
    assert "Account on file: yes" not in prompt


def test_prompt_requires_sequential_function_calls_for_gemini() -> None:
    prompt = build_instructions({"caller_ani": "+19995550123"})

    assert "one tool call at a time" in prompt
    assert "never emit concurrent tool calls" in prompt
