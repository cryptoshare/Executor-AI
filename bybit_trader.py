import os
import logging
from typing import Dict, Any, Optional, List
from pybit.unified_trading import HTTP
from decimal import Decimal, ROUND_DOWN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BybitTrader:
    def __init__(self):
        self.api_key = os.getenv("BYBIT_API_KEY")
        self.api_secret = os.getenv("BYBIT_API_SECRET")
        self.testnet = os.getenv("BYBIT_TESTNET", "true").lower() == "true"
        
        if not self.api_key or not self.api_secret:
            raise ValueError("BYBIT_API_KEY and BYBIT_API_SECRET must be set")
        
        self.client = HTTP(
            testnet=self.testnet,
            api_key=self.api_key,
            api_secret=self.api_secret
        )
        
        logger.info(f"BybitTrader initialized (testnet: {self.testnet})")
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information including balances"""
        try:
            response = self.client.get_wallet_balance(accountType="UNIFIED")
            return response
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information including price precision"""
        try:
            # Use linear perpetual futures only
            response = self.client.get_instruments_info(category="linear", symbol=symbol)
            if response["retCode"] == 0 and response["result"]["list"]:
                return response["result"]["list"][0]
            
            raise ValueError(f"Symbol {symbol} not found in linear perpetual futures")
        except Exception as e:
            logger.error(f"Failed to get symbol info for {symbol}: {e}")
            raise
    
    def place_market_order(self, symbol: str, side: str, qty: float, 
                          stop_loss: Optional[float] = None,
                          take_profit: Optional[float] = None) -> Dict[str, Any]:
        """
        Place a market order with optional stop loss and take profit
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            side: "Buy" or "Sell"
            qty: Quantity to trade
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price
        """
        try:
            # Get symbol info to determine category
            symbol_info = self.get_symbol_info(symbol)
            
            # Get lot size filter for quantity validation
            lot_size_filter = symbol_info.get("lotSizeFilter", {})
            
            if lot_size_filter:
                min_qty = float(lot_size_filter.get("minOrderQty", "0"))
                max_qty = float(lot_size_filter.get("maxOrderQty", "999999"))
                qty_step = float(lot_size_filter.get("qtyStep", "0.001"))
                
                # Ensure quantity meets minimum requirement
                if qty < min_qty:
                    qty = min_qty
                    logger.info(f"Quantity adjusted to minimum: {min_qty}")
                
                # Round to nearest step size
                qty = round(qty / qty_step) * qty_step
                # Ensure clean decimal representation
                qty = float(f"{qty:.1f}")
                
                logger.info(f"Symbol {symbol} - Min: {min_qty}, Max: {max_qty}, Step: {qty_step}, Final Qty: {qty}")
            
            # Prepare order parameters for futures
            order_params = {
                "category": "linear",  # Always use linear perpetual
                "symbol": symbol,
                "side": side,
                "orderType": "Market",
                "qty": str(qty)
            }
            
            # Add stop loss if provided
            if stop_loss:
                order_params["stopLoss"] = str(stop_loss)
            
            # Add take profit if provided
            if take_profit:
                order_params["takeProfit"] = str(take_profit)
            
            logger.info(f"Placing futures order: {order_params}")
            
            response = self.client.place_order(**order_params)
            
            if response["retCode"] == 0:
                logger.info(f"Order placed successfully: {response['result']}")
                return response["result"]
            else:
                logger.error(f"Order placement failed: {response}")
                raise Exception(f"Order placement failed: {response['retMsg']}")
                
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    def place_limit_order(self, symbol: str, side: str, qty: float, price: float,
                         stop_loss: Optional[float] = None,
                         take_profit: Optional[float] = None) -> Dict[str, Any]:
        """
        Place a limit order with optional stop loss and take profit
        """
        try:
            # Get symbol info to determine category
            symbol_info = self.get_symbol_info(symbol)
            category = symbol_info.get("category", "spot")
            
            # Price precision
            price_filter = symbol_info.get("priceFilter", {})
            if price_filter:
                tick_size = float(price_filter.get("tickSize", "0.001"))
                price_precision = len(str(tick_size).split('.')[-1].rstrip('0'))
                price = round(price, price_precision)
            
            # Quantity precision
            lot_size_filter = symbol_info.get("lotSizeFilter", {})
            if lot_size_filter:
                qty_step = float(lot_size_filter.get("qtyStep", "0.001"))
                qty = round(qty / qty_step) * qty_step
                # Ensure clean decimal representation
                qty = float(f"{qty:.1f}")
            
            order_params = {
                "category": "linear",  # Always use linear perpetual
                "symbol": symbol,
                "side": side,
                "orderType": "Limit",
                "qty": str(qty),
                "price": str(price)
            }
            
            if stop_loss:
                order_params["stopLoss"] = str(stop_loss)
            if take_profit:
                order_params["takeProfit"] = str(take_profit)
            
            logger.info(f"Placing limit order: {order_params}")
            
            response = self.client.place_order(**order_params)
            
            if response["retCode"] == 0:
                logger.info(f"Limit order placed successfully: {response['result']}")
                return response["result"]
            else:
                logger.error(f"Limit order placement failed: {response}")
                raise Exception(f"Limit order placement failed: {response['retMsg']}")
                
        except Exception as e:
            logger.error(f"Failed to place limit order: {e}")
            raise
    
    def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Get the status of an order"""
        try:
            response = self.client.get_order_history(
                category="linear",
                symbol=symbol,
                orderId=order_id
            )
            
            if response["retCode"] == 0 and response["result"]["list"]:
                return response["result"]["list"][0]
            else:
                raise ValueError(f"Order {order_id} not found")
                
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            raise
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an existing order"""
        try:
            response = self.client.cancel_order(
                category="linear",
                symbol=symbol,
                orderId=order_id
            )
            
            if response["retCode"] == 0:
                logger.info(f"Order {order_id} cancelled successfully")
                return response["result"]
            else:
                logger.error(f"Order cancellation failed: {response}")
                raise Exception(f"Order cancellation failed: {response['retMsg']}")
                
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise

    def get_positions(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get all open positions for perpetual futures"""
        try:
            params = {
                "category": "linear",
                "settleCoin": "USDT"  # Required parameter for linear perpetual
            }
            if symbol:
                params["symbol"] = symbol
                
            response = self.client.get_positions(**params)
            
            if response["retCode"] == 0:
                logger.info(f"Retrieved {len(response['result']['list'])} positions")
                return response
            else:
                logger.error(f"Failed to get positions: {response}")
                raise Exception(f"Failed to get positions: {response['retMsg']}")
                
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise

    def get_active_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get all active orders for perpetual futures"""
        try:
            params = {
                "category": "linear",
                "settleCoin": "USDT"  # Required parameter for linear perpetual
            }
            if symbol:
                params["symbol"] = symbol
                
            response = self.client.get_open_orders(**params)
            
            if response["retCode"] == 0:
                logger.info(f"Retrieved {len(response['result']['list'])} active orders")
                return response
            else:
                logger.error(f"Failed to get active orders: {response}")
                raise Exception(f"Failed to get active orders: {response['retMsg']}")
                
        except Exception as e:
            logger.error(f"Failed to get active orders: {e}")
            raise

    def get_order_history(self, symbol: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Get order history for perpetual futures"""
        try:
            params = {
                "category": "linear",
                "limit": limit
            }
            if symbol:
                params["symbol"] = symbol
                
            response = self.client.get_order_history(**params)
            
            if response["retCode"] == 0:
                logger.info(f"Retrieved {len(response['result']['list'])} historical orders")
                return response
            else:
                logger.error(f"Failed to get order history: {response}")
                raise Exception(f"Failed to get order history: {response['retMsg']}")
                
        except Exception as e:
            logger.error(f"Failed to get order history: {e}")
            raise

    def get_trade_history(self, symbol: Optional[str] = None, limit: int = 50, 
                         start_time: Optional[int] = None, end_time: Optional[int] = None) -> Dict[str, Any]:
        """Get trade execution history for linear perpetual futures only (not spot)"""
        try:
            params = {
                "category": "linear",
                "limit": limit
            }
            if symbol:
                params["symbol"] = symbol
            if start_time:
                params["startTime"] = start_time
            if end_time:
                params["endTime"] = end_time
                
            response = self.client.get_executions(**params)
            
            if response["retCode"] == 0:
                logger.info(f"Retrieved {len(response['result']['list'])} trade executions")
                return response
            else:
                logger.error(f"Failed to get trade history: {response}")
                raise Exception(f"Failed to get trade history: {response['retMsg']}")
                
        except Exception as e:
            logger.error(f"Failed to get trade history: {e}")
            raise
