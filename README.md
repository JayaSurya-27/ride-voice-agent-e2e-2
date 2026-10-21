# Uber ride-booking voice agent

A local-first LiveKit voice worker for inbound ride booking: Deepgram
speech-to-text, Gemini (via the Gemini API) for the language model, Deepgram Aura
text-to-speech, and Silero voice activity detection.

The application code, prompt, transactional state, tools API, fares, rider data and
Postgres database all run on your machine. LiveKit Cloud remains the media and SIP
control plane, and Deepgram plus Gemini remain model providers.

This version books new rides only. A ride is paid with Uber Cash, or with a saved
card once the caller has confirmed an SMS code during the call.

## Required secrets

The agent needs exactly these five secrets and nothing else:

| Variable | Used for |
|---|---|
| `LIVEKIT_URL` | LiveKit Cloud project URL |
| `LIVEKIT_API_KEY` | LiveKit Cloud API key |
| `LIVEKIT_API_SECRET` | LiveKit Cloud API secret |
| `DEEPGRAM_API_KEY` | Deepgram speech-to-text and Aura text-to-speech |
| `GEMINI_API_KEY` | Gemini API language model (no Vertex / Google Cloud credentials) |

The agent loads them from `.env.local` (`agent/agent.py` calls
`load_dotenv(".env.local")`, and the `agent` Compose service uses
`env_file: .env.local`). Everything else in `.env.example` is a non-secret default.
Never commit `.env.local`.

## What is enforced in code

- Pickup and destination must each be geocoded and explicitly confirmed.
- Fares, availability, surge, and pickup ETAs only come from the tools API.
- Changing an address invalidates the quote, payment choice, and consent token.
- Saved cards require a successful OTP in the current call.
- Uber Cash must cover the high end of the quote.
- Booking requires a one-time token tied to the exact trip read-back and an
  explicit affirmative response.
- Booking writes are idempotent.
- The database stores only card brand and last four digits, never PAN or CVV.

## Tools

`geocode_address`, `confirm_address`, `get_ride_options`, `select_ride_option`,
`get_payment_methods` (saved cards and Uber Cash balance), `send_otp`, `verify_otp`,
`select_payment_method`,
`prepare_booking_confirmation`, `book_ride`, `transfer_to_human`.

## Quick start

Requirements: Docker, Python 3.11–3.13, `uv`, a LiveKit Cloud project, a Deepgram
API key, and a Gemini API key.

1. Create local configuration and fill in the five secrets above:

   ```bash
   cp .env.example .env.local
   ```

2. Start Postgres and the tools API:

   ```bash
   docker compose up -d --build --wait
   curl http://localhost:18090/health
   ```

3. Install and validate the worker:

   ```bash
   uv sync --locked
   uv run python -m livekit.agents download-files
   uv run pytest -q
   ```

4. Talk to it locally in console mode:

   ```bash
   uv run python agent/agent.py console
   ```

   `DEMO_CALLER_ANI` chooses the seeded caller because console sessions have no
   SIP caller-ID attribute. The default is Dana (`+14155550101`). Each seeded
   rider has a fixed demo OTP in `db/seed.sql` (Dana's is `638204`).

5. Run the worker for rooms or telephony:

   ```bash
   uv run python agent/agent.py dev
   ```

   For a completely containerized application runtime:

   ```bash
   docker compose --profile full up --build
   ```

## Seeded scenarios

| Caller | Expected path |
|---|---|
| `+14155550101` Dana | Valid saved Visa; OTP required. Uber Cash 60.00 |
| `+14155550102` Marcus | Expired card; Uber Cash 65.00 can cover many trips |
| `+14155550103` Priya | Suspended; booking rejected and human handoff offered |
| `+14155550105` Maya | Uber Cash 6.25; balance too low for most trips |
| Any other number | No account; no booking, transfer offered |

Useful spoken places include “Hilton Union Square,” “SFO International,” “two
hundred Market Street,” “Ferry Building,” and “Oakland airport.” “Main Street”
returns multiple cities on purpose so address disambiguation can be tested.

## Inbound phone setup

Install LiveKit CLI 2.15 or newer and authenticate it:

```bash
brew install livekit-cli
lk cloud auth
lk app env -w -d .env.local
```

Create or connect an inbound SIP trunk/LiveKit phone number, then apply the
included individual dispatch rule (one isolated room per caller):

```bash
lk sip dispatch create telephony/dispatch-rule.json
```

## Verification and reset

Run deterministic unit tests only:

```bash
uv run pytest -q
```

Run the same tests plus the real container API/database flow:

```bash
RUN_INTEGRATION=1 uv run pytest -q
```

Format and lint:

```bash
uv run ruff format --check .
uv run ruff check .
```

Stop services while retaining demo data:

```bash
docker compose down
```

To deliberately erase and reseed the demo database, run
`docker compose down --volumes` and then `docker compose up -d --build`.
