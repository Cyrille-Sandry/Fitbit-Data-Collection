-- Table des “steps” (pas) par date (agrégés journaliers)
CREATE TABLE IF NOT EXISTS daily_steps (
  user_id TEXT NOT NULL,
  date DATE NOT NULL,
  steps INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, date)
);

-- Table du rythme cardiaque “au repos” (journalier, si disponible)
CREATE TABLE IF NOT EXISTS daily_resting_hr (
  user_id TEXT NOT NULL,
  date DATE NOT NULL,
  resting_hr INTEGER,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, date)
);

-- Table “raw” pour stocker le JSON brut (audit/troubleshooting)
CREATE TABLE IF NOT EXISTS raw_fitbit_responses (
  user_id TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  date DATE NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, endpoint, date)
);
