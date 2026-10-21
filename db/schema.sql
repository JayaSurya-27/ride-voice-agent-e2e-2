-- Uber ride-booking voice agent — schema mirrors §3a of the prompt package.
-- Every fare/ETA/availability the agent speaks must come from here via a tool.

DROP TABLE IF EXISTS bookings, wallets, users, products, market_config, places CASCADE;

-- §3a users
CREATE TABLE users (
    rider_id            TEXT PRIMARY KEY,
    phone               TEXT UNIQUE NOT NULL,          -- E.164, matched against caller_ani
    first_name          TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'active' -- active|suspended|payment_hold|banned
                        CHECK (status IN ('active','suspended','payment_hold','banned')),
    phone_verified      BOOLEAN NOT NULL DEFAULT TRUE,
    rating              NUMERIC(2,1) DEFAULT 4.8,
    default_market      TEXT NOT NULL DEFAULT 'US-SF',
    home_city           TEXT,
    preferred_language  TEXT NOT NULL DEFAULT 'en',
    business_profile_id TEXT,
    accessibility_needs TEXT[] DEFAULT '{}'            -- e.g. {wav}
);

CREATE TABLE wallets (
    rider_id          TEXT PRIMARY KEY REFERENCES users(rider_id) ON DELETE CASCADE,
    uber_cash_balance NUMERIC(10,2) NOT NULL DEFAULT 0
);

-- Geocoding source. geocode_address() searches formatted_address + aliases,
-- so "the Hilton on Union Square" resolves without a real Places API.
CREATE TABLE places (
    place_id          TEXT PRIMARY KEY,
    formatted_address TEXT NOT NULL,
    city              TEXT NOT NULL,
    market            TEXT NOT NULL,
    lat               NUMERIC(9,6) NOT NULL,
    lng               NUMERIC(9,6) NOT NULL,
    aliases           TEXT[] DEFAULT '{}'
);

-- Ride tiers. Fares are COMPUTED from these + distance, never invented.
CREATE TABLE products (
    product_id   TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    capacity     INT  NOT NULL,
    base_fare    NUMERIC(10,2) NOT NULL,
    per_mile     NUMERIC(10,2) NOT NULL,
    per_minute   NUMERIC(10,2) NOT NULL,
    min_fare     NUMERIC(10,2) NOT NULL,
    description  TEXT,
    is_wav       BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order   INT NOT NULL DEFAULT 0
);

-- §3d business config, per market
CREATE TABLE market_config (
    market          TEXT PRIMARY KEY,
    currency        TEXT NOT NULL DEFAULT 'USD',
    surge_multiplier NUMERIC(3,2) NOT NULL DEFAULT 1.00,
    available_products TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE bookings (
    booking_ref       TEXT PRIMARY KEY,
    rider_id          TEXT,
    pickup_place_id   TEXT NOT NULL,
    dropoff_place_id  TEXT NOT NULL,
    product_id        TEXT NOT NULL,
    payment_method    TEXT NOT NULL,
    quoted_fare_low   NUMERIC(10,2) NOT NULL,
    quoted_fare_high  NUMERIC(10,2) NOT NULL,
    status            TEXT NOT NULL DEFAULT 'matched',
    driver_name       TEXT,
    vehicle           TEXT,
    plate             TEXT,
    eta_pickup_min    INT,
    idempotency_key    TEXT UNIQUE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
