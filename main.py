
import os, hmac, hashlib, json, uuid, datetime
from typing import Any, Dict
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from jsonschema import validate, ValidationError

# Import Bybit trader
try:
    from bybit_trader import BybitTrader
    BYBIT_AVAILABLE = True
except ImportError:
    BYBIT_AVAILABLE = False
    print("[WARN] Bybit trader not available - install pybit for trading")

# Optional Supabase insert (only if env vars are present)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        print("[WARN] Supabase client not initialized:", e)

# Load schema on boot
SCHEMA_PATH = os.getenv("DECISION_SCHEMA_PATH", "decision_schema.json")
with open(SCHEMA_PATH, "r") as f:
    DECISION_SCHEMA = json.load(f)

WEBHOOK_SECRET = os.getenv("EXECUTOR_WEBHOOK_SECRET", "")

# Initialize Bybit trader if credentials are available
bybit_trader = None
if BYBIT_AVAILABLE:
    try:
        bybit_trader = BybitTrader()
        print("[INFO] Bybit trader initialized successfully")
    except Exception as e:
        print(f"[WARN] Bybit trader initialization failed: {e}")
        bybit_trader = None

app = FastAPI(title="Trade Executor (Starter)", version="0.1.0")

def verify_signature(raw_body: bytes, header_sig: str | None) -> None:
    """
    Verify HMAC signature if EXECUTOR_WEBHOOK_SECRET is set.
    If no secret set, allow (for first-time testing).
    """
    if not WEBHOOK_SECRET:
        return
    if not header_sig:
        raise HTTPException(status_code=401, detail="Missing X-Signature")
    calc = hmac.new(WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    # Constant-time compare
    if not hmac.compare_digest(calc, header_sig):
        raise HTTPException(status_code=401, detail="Invalid signature")

def validate_payload(payload: Dict[str, Any]) -> None:
    try:
        validate(instance=payload, schema=DECISION_SCHEMA)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Schema validation error: {e.message}")

def insert_signal(payload: Dict[str, Any], trade_id: str, status: str) -> None:
    if not supabase:
        return
    try:
        supabase.table("signals").insert({
            "id": trade_id,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "symbol": payload.get("symbol"),
            "status": status,
            "raw": payload
        }).execute()
    except Exception as e:
        print("[WARN] Supabase insert failed:", e)

def execute_trade(payload: Dict[str, Any], trade_id: str) -> Dict[str, Any]:
    """
    Execute a trade based on the decision payload
    """
    if not bybit_trader:
        raise HTTPException(status_code=503, detail="Trading not available - Bybit credentials not configured")
    
    try:
        symbol = payload.get("symbol")
        side = payload.get("side")
        risk_plan = payload.get("risk_plan", {})
        
        # Convert symbol format (e.g., "HYPE/USDT" -> "HYPEUSDT")
        symbol = symbol.replace("/", "")
        
        # Determine order side
        if side == "long":
            order_side = "Buy"
        elif side == "short":
            order_side = "Sell"
        else:
            raise ValueError(f"Invalid side: {side}")
        
        # Get position size from risk plan
        position_usd = risk_plan.get("position_usd", 0)
        if position_usd <= 0:
            raise ValueError("Invalid position size")
        
        # Get current price to calculate quantity
        try:
            # Get current ticker price from futures
            ticker_response = bybit_trader.client.get_tickers(category="linear", symbol=symbol)
            if ticker_response["retCode"] == 0 and ticker_response["result"]["list"]:
                current_price = float(ticker_response["result"]["list"][0]["lastPrice"])
                # Calculate quantity based on USD amount
                qty = position_usd / current_price
                
                # Get symbol info to adjust quantity to proper step size
                symbol_info = bybit_trader.get_symbol_info(symbol)
                lot_size_filter = symbol_info.get("lotSizeFilter", {})
                
                if lot_size_filter:
                    min_qty = float(lot_size_filter.get("minOrderQty", "0"))
                    qty_step = float(lot_size_filter.get("qtyStep", "0.001"))
                    
                    # Ensure quantity meets minimum requirement
                    if qty < min_qty:
                        qty = min_qty
                        print(f"[INFO] Quantity adjusted to minimum: {min_qty}")
                    
                    # Round to nearest step size
                    qty = round(qty / qty_step) * qty_step
                    # Ensure clean decimal representation
                    qty = float(f"{qty:.1f}")
                    print(f"[INFO] Final quantity: {qty} (step: {qty_step})")
            else:
                # Fallback: use minimum quantity
                qty = 0.1
                print(f"[WARN] Could not get current price for {symbol}, using minimum quantity")
        except Exception as e:
            print(f"[WARN] Error getting current price: {e}, using minimum quantity")
            qty = 0.1
        
        entry_plan = risk_plan.get("entry_plan", {})
        entry_type = entry_plan.get("type", "market")
        
        # Get stop loss and take profit
        stop_loss = risk_plan.get("stop_loss")
        take_profits = risk_plan.get("take_profits", [])
        take_profit = take_profits[0].get("price") if take_profits else None
        
        if entry_type == "market":
            # Place market order
            order_result = bybit_trader.place_market_order(
                symbol=symbol,
                side=order_side,
                qty=qty,  # Use calculated quantity
                stop_loss=stop_loss,
                take_profit=take_profit
            )
        elif entry_type == "limit":
            entries = entry_plan.get("entries", [])
            if not entries:
                raise ValueError("No entries specified for limit order")
            
            entry = entries[0]  # Use first entry for now
            price = entry.get("price")
            size_frac = entry.get("size_frac", 1.0)
            
            order_result = bybit_trader.place_limit_order(
                symbol=symbol,
                side=order_side,
                qty=position_usd * size_frac,  # This should be quantity
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
        else:
            raise ValueError(f"Unsupported entry type: {entry_type}")
        
        return {
            "order_id": order_result.get("orderId"),
            "symbol": symbol,
            "side": order_side,
            "status": order_result.get("orderStatus"),
            "executed_qty": order_result.get("execQty"),
            "executed_price": order_result.get("avgPrice")
        }
        
    except Exception as e:
        print(f"[ERROR] Trade execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Trade execution failed: {str(e)}")

@app.get("/v1/healthz")
def health():
    return {"ok": True, "ts": datetime.datetime.utcnow().isoformat() + "Z"}

@app.get("/v1/account")
def account_status():
    """Get account information and trading status"""
    if not bybit_trader:
        return {
            "trading_available": False,
            "message": "Bybit credentials not configured"
        }
    
    try:
        account_info = bybit_trader.get_account_info()
        return {
            "trading_available": True,
            "account_info": account_info
        }
    except Exception as e:
        return {
            "trading_available": False,
            "error": str(e)
        }

@app.post("/v1/execute")
async def execute(request: Request):
    raw = await request.body()
    sig = request.headers.get("X-Signature")
    verify_signature(raw, sig)

    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    validate_payload(payload)

    decision = payload.get("decision")
    if decision not in ("enter", "skip"):
        raise HTTPException(status_code=400, detail="decision must be 'enter' or 'skip'")

    trade_id = str(uuid.uuid4())

    if decision == "enter":
        # Execute the trade
        try:
            order_result = execute_trade(payload, trade_id)
            status = "executed"
            print(f"[EXECUTOR] Trade executed successfully: {order_result}")
        except Exception as e:
            status = "failed"
            print(f"[EXECUTOR] Trade execution failed: {e}")
            order_result = {"error": str(e)}
    else:
        # Skip the trade
        status = "skipped"
        order_result = None

    # Log to Supabase
    insert_signal(payload, trade_id, status)

    print(f"[EXECUTOR] Received decision={decision}, trade_id={trade_id}, status={status}")
    
    response_data = {
        "status": "accepted" if status != "failed" else "failed",
        "trade_id": trade_id,
        "decision": decision,
        "execution_status": status
    }
    
    if order_result:
        response_data["order_details"] = order_result
    
    return JSONResponse(response_data)

@app.get("/")
def root():
    return {"service": "Trade Executor (Starter)", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
