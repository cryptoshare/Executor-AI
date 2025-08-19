
-- Minimal tables for starter
create table if not exists public.signals (
  id uuid primary key,
  created_at timestamptz default now(),
  symbol text,
  status text,
  raw jsonb
);

create table if not exists public.trades (
  id uuid primary key,
  signal_id uuid,
  symbol text,
  state text,
  dir text,
  entry numeric,
  sl numeric,
  tp jsonb[],
  size_usd numeric,
  opened_at timestamptz,
  closed_at timestamptz,
  pnl_usd numeric,
  tags text[]
);

create table if not exists public.orders (
  id uuid primary key,
  trade_id uuid,
  venue text,
  type text,
  qty numeric,
  price numeric,
  status text,
  tx_hash text,
  meta jsonb,
  created_at timestamptz default now()
);
