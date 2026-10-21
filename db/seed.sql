-- Seed data. Uber Cash is the only payment method:
--   +14155550101 Dana   — known rider, Uber Cash 60.00 -> books most city trips
--   +14155550102 Marcus — known rider, Uber Cash 65.00
--   +14155550103 Priya  — suspended account            -> must refuse to book
--   anything else       — unknown number -> no booking, transfer offered

INSERT INTO market_config (market, currency, surge_multiplier, available_products) VALUES
  ('US-SF',  'USD', 1.00, ARRAY['uberx','comfort','uberxl','black','wav']),
  ('US-NYC', 'USD', 1.35, ARRAY['uberx','comfort','uberxl','black']),
  ('IN-BLR', 'INR', 1.00, ARRAY['uberx','uberxl']);

INSERT INTO products (product_id, display_name, capacity, base_fare, per_mile, per_minute, min_fare, description, is_wav, sort_order) VALUES
  ('uberx',   'UberX',   4, 2.55, 1.75, 0.35,  8.00, 'Affordable everyday rides',        FALSE, 1),
  ('comfort', 'Comfort', 4, 3.50, 2.10, 0.45, 11.00, 'Newer cars, extra legroom',        FALSE, 2),
  ('uberxl',  'UberXL',  6, 4.20, 2.60, 0.50, 14.00, 'Room for up to six',               FALSE, 3),
  ('black',   'Black',   4, 8.00, 4.10, 0.75, 26.00, 'Premium rides, professional drivers', FALSE, 4),
  ('wav',     'UberWAV', 4, 2.55, 1.75, 0.35,  8.00, 'Wheelchair-accessible vehicle',    TRUE,  5);

INSERT INTO places (place_id, formatted_address, city, market, lat, lng, aliases) VALUES
  ('plc_hilton_us',  '333 O''Farrell Street, San Francisco, CA', 'San Francisco', 'US-SF', 37.785980, -122.410140,
     ARRAY['hilton','hilton union square','the hilton on union square','union square hilton']),
  ('plc_sfo_intl',   'SFO International Terminal, San Francisco, CA', 'San Francisco', 'US-SF', 37.615223, -122.389977,
     ARRAY['sfo','sfo international','the airport','san francisco airport','international terminal']),
  ('plc_200_market', '200 Market Street, San Francisco, CA', 'San Francisco', 'US-SF', 37.793750, -122.396990,
     ARRAY['200 market','200 market street','market street']),
  ('plc_15_market',  '15 Market Street, San Francisco, CA', 'San Francisco', 'US-SF', 37.792100, -122.395400,
     ARRAY['15 market','fifteen market street']),
  ('plc_ferry_bldg', 'Ferry Building, San Francisco, CA', 'San Francisco', 'US-SF', 37.795530, -122.393300,
     ARRAY['ferry building','the ferry building','embarcadero']),
  ('plc_home_dana',  '1200 Guerrero Street, San Francisco, CA', 'San Francisco', 'US-SF', 37.751900, -122.422600,
     ARRAY['guerrero','1200 guerrero']),
  ('plc_work_dana',  '1455 Market Street, San Francisco, CA', 'San Francisco', 'US-SF', 37.775600, -122.417100,
     ARRAY['1455 market','the office']),
  ('plc_main_st_sf', 'Main Street, San Francisco, CA', 'San Francisco', 'US-SF', 37.791400, -122.392600,
     ARRAY['main street']),
  ('plc_main_st_la', 'Main Street, Los Angeles, CA', 'Los Angeles', 'US-LA', 34.050400, -118.242000,
     ARRAY['main street']),
  ('plc_oak_air',    'Oakland International Airport, Oakland, CA', 'Oakland', 'US-SF', 37.712600, -122.212000,
     ARRAY['oakland airport','oak']),
  ('plc_maya_home', '1890 Jefferson Street, San Francisco, CA', 'San Francisco', 'US-SF', 37.804600, -122.442300,
     ARRAY['1890 jefferson','jefferson street','marina home']),
  ('plc_mission_dolores', 'Mission Dolores Park, 19th Street, San Francisco, CA', 'San Francisco', 'US-SF', 37.759600, -122.426900,
     ARRAY['mission dolores','dolores park','mission dolores park']),
  ('plc_ucsf_parnassus', 'UCSF Medical Center, 505 Parnassus Avenue, San Francisco, CA', 'San Francisco', 'US-SF', 37.763100, -122.458600,
     ARRAY['ucsf parnassus','ucsf medical center','505 parnassus']),
  ('plc_caltrain', 'San Francisco Caltrain Station, 700 4th Street, San Francisco, CA', 'San Francisco', 'US-SF', 37.776400, -122.394300,
     ARRAY['caltrain','fourth and king','4th and king','700 fourth street']),
  ('plc_chase_center', 'Chase Center, 1 Warriors Way, San Francisco, CA', 'San Francisco', 'US-SF', 37.768000, -122.387700,
     ARRAY['chase center','the arena','warriors way']),
  ('plc_225_mission_sf', '225 Mission Street, San Francisco, CA', 'San Francisco', 'US-SF', 37.790500, -122.396800,
     ARRAY['mission street','225 mission','fremont street office']),
  ('plc_mission_santa_cruz', 'Mission Street, Santa Cruz, CA', 'Santa Cruz', 'US-SF', 36.974100, -122.030800,
     ARRAY['mission street','santa cruz mission']);

INSERT INTO users (rider_id, phone, first_name, status, phone_verified, rating, default_market, home_city, preferred_language) VALUES
  ('rdr_dana',   '+14155550101', 'Dana',   'active',    TRUE, 4.9, 'US-SF', 'San Francisco', 'en'),
  ('rdr_marcus', '+14155550102', 'Marcus', 'active',    TRUE, 4.6, 'US-SF', 'San Francisco', 'en'),
  ('rdr_priya',  '+14155550103', 'Priya',  'suspended', TRUE, 4.2, 'US-SF', 'San Francisco', 'en'),
  ('rdr_arjun',  '+919845550104','Arjun',  'active',    TRUE, 4.7, 'IN-BLR','Bengaluru',     'en'),
  ('rdr_maya',   '+14155550105', 'Maya',   'active',    TRUE, 4.8, 'US-SF', 'San Francisco', 'en'),
  ('rdr_jorge',  '+14155550106', 'Jorge',  'active',    TRUE, 4.7, 'US-SF', 'San Francisco', 'es'),
  ('rdr_eli',    '+14155550108', 'Eli',    'active',    TRUE, 4.5, 'US-SF', 'Oakland',       'en'),
  ('rdr_kenji',  '+14155550109', 'Kenji',  'active',    TRUE, 4.9, 'US-SF', 'San Francisco', 'ja');

INSERT INTO wallets (rider_id, uber_cash_balance) VALUES
  ('rdr_dana', 60.00), ('rdr_marcus', 65.00), ('rdr_priya', 0.00), ('rdr_arjun', 0.00),
  ('rdr_maya', 6.25), ('rdr_jorge', 80.00), ('rdr_eli', 3.15), ('rdr_kenji', 0.00);
