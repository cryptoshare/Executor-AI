
# Trade Executor (Starter)

Minimal FastAPI service that accepts a **decision JSON** from ChatGPT/Make and
acknowledges it. HMAC verification is included; Supabase logging is optional.

## 1) Environment variables

- `EXECUTOR_WEBHOOK_SECRET`  — shared secret with Make (optional for first run)
- `PORT` — Railway sets this automatically
- (optional) `SUPABASE_URL`
- (optional) `SUPABASE_SERVICE_ROLE_KEY`
- (optional) `DECISION_SCHEMA_PATH` — path to `decision_schema.json`

### Bybit Trading Integration
- `BYBIT_API_KEY` — Your Bybit API key
- `BYBIT_API_SECRET` — Your Bybit API secret
- `BYBIT_TESTNET` — Set to "true" for testnet, "false" for mainnet (default: "true")

## 2) Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export EXECUTOR_WEBHOOK_SECRET=$(python - <<'PY' 
import secrets;print(secrets.token_hex(32)) 
PY
)
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 3) Test with cURL (with HMAC)

```bash
# sample payload
cat > payload.json <<'JSON'
{
  "ts": "2025-08-19T11:43:46.912297Z",
  "symbol": "HYPE/USDT",
  "decision": "enter",
  "allow_new_trades": true,
  "side": "long",
  "confidence": 0.7,
  "reasons": ["test"],
  "denied_reasons": [],
  "risk_plan": {
    "position_usd": 2000,
    "max_risk_pct_equity": 0.5,
    "entry_plan": {
      "type": "market",
      "entries": [{"price": 41.1, "size_frac": 1.0}],
      "cancel_if": {"timeout_sec": 3600}
    },
    "stop_loss": 40.3,
    "take_profits": [{"price": 41.7, "close_frac": 1.0}],
    "trail": {}
  },
  "compliance": {"cooldown_min": 45},
  "scores": {"trend_align": 0.8},
  "rr": 2.0
}
JSON

# compute signature
SIG=$(python - <<'PY'
import hmac,hashlib,os,sys,json
secret=os.environ.get("EXECUTOR_WEBHOOK_SECRET","").encode()
body=open("payload.json","rb").read()
print(hmac.new(secret, body, hashlib.sha256).hexdigest())
PY
)

# send
curl -sS -X POST "http://127.0.0.1:8000/v1/execute"   -H "Content-Type: application/json"   -H "X-Signature: $SIG"   --data-binary @payload.json | jq .
```

## 4) Deploy on Railway

### Option A: Deploy from GitHub Repository
1. Push this code to your GitHub repository
2. Go to [Railway](https://railway.app) and create a new project
3. Select **Deploy from GitHub repo**
4. Choose your repository (e.g., `cryptoshare/Executor-AI`)
5. Railway will automatically detect the Python app and use the `Procfile`

### Option B: Manual Deployment
1. Create a new **Service → Deploy from Repo** (or upload these files to a repository).
2. Set **Start Command**:  
   `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Add **Variables**:  
   - `EXECUTOR_WEBHOOK_SECRET = <paste your generated hex>`  
   - (optional) `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
   - (optional) `BYBIT_API_KEY`, `BYBIT_API_SECRET`, and `BYBIT_TESTNET` for trading
4. Redeploy; copy the service URL, e.g. `https://your-app.up.railway.app`.

## 5) Make.com → HTTP POST

- Method: POST  
- URL: `https://your-app.up.railway.app/v1/execute`  
- Body: raw JSON from the Assistant (decision JSON)  
- Header `Content-Type: application/json`  
- Header `X-Signature: <hex HMAC of body>`

To create the signature in Make:
- Module: **Crypto → Create a HMAC**
  - Message: the raw JSON string
  - Secret: your `EXECUTOR_WEBHOOK_SECRET`
  - Algorithm: SHA-256
  - Output: Hex

## 6) Optional Supabase table (signals)

```sql
create table if not exists public.signals (
  id uuid primary key,
  created_at timestamptz default now(),
  symbol text,
  status text,
  raw jsonb
);
```

> If `SUPABASE_URL` & `SUPABASE_SERVICE_ROLE_KEY` are set, the service will insert a row into `signals` on each POST.

## 7) Trading Execution

### Without Bybit Integration (Starter Mode)
If no Bybit credentials are provided, the executor will only acknowledge decisions without placing actual trades.

### With Bybit Integration
When `BYBIT_API_KEY` and `BYBIT_API_SECRET` are configured:

**For "enter" decisions:**
- Executes actual trades on Bybit
- Supports market and limit orders
- Includes stop-loss and take-profit orders
- Returns detailed order information

**Response example:**
```json
{
  "status": "accepted",
  "trade_id": "550e8400-e29b-41d4-a716-446655440000",
  "decision": "enter",
  "execution_status": "executed",
  "order_details": {
    "order_id": "123456789",
    "symbol": "HYPEUSDT",
    "side": "Buy",
    "status": "Filled",
    "executed_qty": "48.5",
    "executed_price": "41.2"
  }
}
```

### Account Status
Check trading availability: `GET /v1/account`

### Trade History
Get perpetual trade execution history: `GET /v1/trade-history`

**Query Parameters:**
- `symbol` (optional): Filter by trading pair (e.g., "BTCUSDT")
- `limit` (optional): Number of trades to return (1-1000, default: 50)
- `start_time` (optional): Start timestamp in milliseconds
- `end_time` (optional): End timestamp in milliseconds

**Example:**
```bash
curl "https://your-app.up.railway.app/v1/trade-history?symbol=BTCUSDT&limit=100"
```

**Response:**
```json
{
  "trading_available": true,
  "timestamp": "2025-01-17T12:00:00.000Z",
  "query_params": {
    "symbol": "BTCUSDT",
    "limit": 100,
    "start_time": null,
    "end_time": null
  },
  "trades": {
    "count": 25,
    "list": [
      {
        "symbol": "BTCUSDT",
        "side": "Buy",
        "executed_price": "45000.5",
        "executed_qty": "0.1",
        "executed_value": "4500.05",
        "executed_fee": "2.25",
        "executed_time": "1705507200000",
        "order_id": "123456789",
        "order_link_id": "",
        "is_maker": false,
        "trade_id": "exec_123456"
      }
    ]
  }
}
```

### Important Notes
- **Always test with testnet first** (`BYBIT_TESTNET=true`)
- Ensure your API keys have trading permissions
- Monitor your positions and orders regularly
- The executor converts symbol format (e.g., "HYPE/USDT" → "HYPEUSDT")
