from __future__ import annotations

from typing import Literal

from livekit.agents import Agent, RunContext, function_tool
from livekit.agents.llm import ToolError

from .prompt import build_instructions
from .state import BookingState, GuardError
from .tools_client import ToolsAPIError, ToolsClient


def _tool_error(exc: Exception) -> ToolError:
    if isinstance(exc, (GuardError, ToolsAPIError)):
        return ToolError(str(exc))
    return ToolError("That action could not be completed. Offer to retry or transfer.")


class RideBookingAgent(Agent):
    """LiveKit agent whose tools enforce the transactional state machine."""

    def __init__(self, state: BookingState, client: ToolsClient, context: dict) -> None:
        self.state = state
        self.client = client
        self.context = context
        super().__init__(instructions=build_instructions(context))

    async def on_enter(self) -> None:
        if self.state.rider_status in {"suspended", "payment_hold", "banned"}:
            status = self.state.rider_status.replace("_", " ")
            await self.client.call(
                "transfer_to_human", reason=f"account {self.state.rider_status}"
            )
            self.session.say(
                f"There is a {status} on your account, so I cannot book a ride. "
                "I am transferring you to a human agent now.",
                allow_interruptions=False,
            )
            return
        if self.state.rider_id and self.state.first_name:
            greeting = (
                f"Hi {self.state.first_name}, thanks for calling Uber. "
                "Where should the driver pick you up?"
            )
        else:
            greeting = (
                "Hi, thanks for calling Uber. I can only book rides for riders with "
                "an Uber account on this phone number. Would you like me to transfer "
                "you to a human agent?"
            )
        await self.session.generate_reply(
            instructions=f'Say exactly this greeting: "{greeting}"',
            allow_interruptions=True,
        )

    @function_tool()
    async def geocode_address(
        self, query: str, address_kind: Literal["pickup", "dropoff"]
    ) -> dict:
        """Find candidates for a spoken pickup or dropoff. Read one back before confirming it."""
        try:
            result = await self.client.call(
                "geocode_address",
                query=query,
                market=self.state.default_market,
                _trace_payload={"address_kind": address_kind},
            )
            self.state.remember_geocode(address_kind, result.get("candidates", []))
            return result
        except Exception as exc:
            raise _tool_error(exc) from exc

    @function_tool()
    async def confirm_address(
        self, address_kind: Literal["pickup", "dropoff"], place_id: str
    ) -> dict:
        """Record that the caller explicitly confirmed one latest geocoded candidate."""
        try:
            candidate = self.state.confirm_address(address_kind, place_id)
            result = {
                "confirmed": True,
                "address_kind": address_kind,
                "formatted_address": candidate["formatted_address"],
            }
            if self.client.harness_mode:
                self.client.record_local(
                    "confirm_address",
                    {"address_kind": address_kind, "place_id": place_id},
                    result,
                )
            return result
        except Exception as exc:
            raise _tool_error(exc) from exc

    @function_tool()
    async def get_ride_options(self) -> dict:
        """Get fresh fares, pickup ETAs, availability, distance, and surge after both addresses are confirmed."""
        try:
            self.state.ensure_bookable()
            if not self.state.pickup or not self.state.dropoff:
                raise GuardError(
                    "Confirm pickup and destination before requesting options."
                )
            result = await self.client.call(
                "get_ride_options",
                pickup_place_id=self.state.pickup["place_id"],
                dropoff_place_id=self.state.dropoff["place_id"],
                rider_id=self.state.rider_id,
                accessibility_needs=self.state.accessibility_needs,
            )
            self.state.remember_quote(result)
            return result
        except Exception as exc:
            raise _tool_error(exc) from exc

    @function_tool()
    async def select_ride_option(self, product_id: str) -> dict:
        """Freeze one available product and its fare range from the latest quote."""
        try:
            option = self.state.select_product(product_id)
            if self.client.harness_mode:
                result = {"selected": True, "option": option}
                self.client.record_local(
                    "select_ride_option", {"product_id": product_id}, result
                )
                return result
            return {"selected": True, "option": option}
        except Exception as exc:
            raise _tool_error(exc) from exc

    @function_tool()
    async def get_payment_methods(self) -> dict:
        """Get safe saved-card metadata and the Uber Cash balance; never returns full card details."""
        if not self.state.rider_id:
            return {"methods": [], "uber_cash_balance": 0}
        try:
            result = await self.client.call(
                "get_payment_methods", rider_id=self.state.rider_id
            )
            self.state.payment_methods = result.get("methods", [])
            self.state.uber_cash_balance = float(result.get("uber_cash_balance", 0))
            return result
        except Exception as exc:
            raise _tool_error(exc) from exc

    @function_tool()
    async def send_otp(self) -> dict:
        """Send an SMS verification code to the caller before using a saved card."""
        try:
            return await self.client.call("send_otp", phone=self.state.caller_ani)
        except Exception as exc:
            raise _tool_error(exc) from exc

    @function_tool()
    async def verify_otp(self, code: str) -> dict:
        """Verify the caller's SMS code. Never infer or guess a code."""
        try:
            result = await self.client.call(
                "verify_otp", phone=self.state.caller_ani, code=code
            )
            if result.get("verified"):
                self.state.auth_level = "otp_verified"
            return result
        except Exception as exc:
            raise _tool_error(exc) from exc

    @function_tool()
    async def select_payment_method(self, payment_method: str) -> dict:
        """Select saved_card:<id> or uber_cash after explaining it."""
        try:
            self.state.select_payment(payment_method)
            if self.client.harness_mode:
                result = {"selected": True, "payment": payment_method}
                self.client.record_local(
                    "select_payment_method",
                    {"payment_method": payment_method},
                    result,
                )
                return result
            return {"selected": True, "payment": payment_method}
        except Exception as exc:
            raise _tool_error(exc) from exc

    @function_tool()
    async def prepare_booking_confirmation(self) -> dict:
        """Create the exact final trip read-back and one-time token. Read the summary, then ask for an explicit yes."""
        try:
            token, summary = self.state.prepare_confirmation()
            if self.client.harness_mode:
                result = {"confirmation_token": token, "summary_to_read": summary}
                self.client.record_local("prepare_booking_confirmation", {}, result)
                return result
            return {"confirmation_token": token, "summary_to_read": summary}
        except Exception as exc:
            raise _tool_error(exc) from exc

    @function_tool()
    async def book_ride(
        self,
        context: RunContext,
        confirmation_token: str,
        caller_explicitly_confirmed: bool,
    ) -> dict:
        """Book only after reading the prepared summary and hearing an explicit yes from the caller."""
        context.disallow_interruptions()
        try:
            self.state.authorize_booking(confirmation_token, caller_explicitly_confirmed)
            snapshot = self.state.snapshot()
            result = await self.client.call(
                "book_ride",
                rider_id=self.state.rider_id,
                pickup_place_id=snapshot["pickup_place_id"],
                dropoff_place_id=snapshot["dropoff_place_id"],
                product_id=snapshot["product_id"],
                payment_method=snapshot["payment_method"],
                quoted_fare_low=snapshot["fare_low"],
                quoted_fare_high=snapshot["fare_high"],
                idempotency_key=confirmation_token,
                _trace_payload={
                    "confirmation_token": confirmation_token,
                    "caller_explicitly_confirmed": caller_explicitly_confirmed,
                },
            )
            self.state.booking_ref = result.get("booking_ref")
            return result
        except Exception as exc:
            raise _tool_error(exc) from exc

    @function_tool()
    async def transfer_to_human(self, reason: str) -> dict:
        """Request a human handoff for unsupported, account-blocked, safety, or failed-service cases."""
        try:
            return await self.client.call("transfer_to_human", reason=reason)
        except Exception as exc:
            raise _tool_error(exc) from exc
