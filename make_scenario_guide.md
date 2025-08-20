# Make.com Railway Endpoint Testing Guide

## 🚀 **Complete Make.com Scenario Setup**

### **Scenario 1: Basic Endpoint Testing**

#### **Step 1: HTTP - Health Check**
```
Module: HTTP → Make an HTTP request
Method: GET
URL: {{your_railway_url}}/v1/healthz
Headers:
  Content-Type: application/json
Timeout: 30 seconds
```

#### **Step 2: HTTP - Account Status**
```
Module: HTTP → Make an HTTP request
Method: GET
URL: {{your_railway_url}}/v1/account
Headers:
  Content-Type: application/json
Timeout: 30 seconds
```

#### **Step 3: HTTP - Root Endpoint**
```
Module: HTTP → Make an HTTP request
Method: GET
URL: {{your_railway_url}}/
Headers:
  Content-Type: application/json
Timeout: 30 seconds
```

#### **Step 4: Text Aggregator - Results Summary**
```
Module: Text Aggregator
Text: |
  🚀 Railway Endpoint Test Results
  ===============================
  
  Health Check: {{1.status}} - {{1.body.ok}}
  Account Status: {{2.status}} - Trading Available: {{2.body.trading_available}}
  Root Endpoint: {{3.status}} - Service: {{3.body.service}}
  
  Timestamp: {{formatDate(now; "YYYY-MM-DD HH:mm:ss")}}
```

### **Scenario 2: Advanced Testing with Error Handling**

#### **Step 1: Set Variable - Base URL**
```
Module: Set Variable
Variable Name: railway_url
Value: https://your-app-name.up.railway.app
```

#### **Step 2: Router - Test Different Endpoints**
```
Module: Router
Routes:
  - Health Check
  - Account Status  
  - Root Endpoint
  - API Docs
```

#### **Step 3: HTTP - Health Check (Route 1)**
```
Module: HTTP → Make an HTTP request
Method: GET
URL: {{railway_url}}/v1/healthz
Headers:
  Content-Type: application/json
Timeout: 30 seconds
```

#### **Step 4: HTTP - Account Status (Route 2)**
```
Module: HTTP → Make an HTTP request
Method: GET
URL: {{railway_url}}/v1/account
Headers:
  Content-Type: application/json
Timeout: 30 seconds
```

#### **Step 5: HTTP - Root Endpoint (Route 3)**
```
Module: HTTP → Make an HTTP request
Method: GET
URL: {{railway_url}}/
Headers:
  Content-Type: application/json
Timeout: 30 seconds
```

#### **Step 6: HTTP - API Documentation (Route 4)**
```
Module: HTTP → Make an HTTP request
Method: GET
URL: {{railway_url}}/docs
Headers:
  Content-Type: text/html
Timeout: 30 seconds
```

#### **Step 7: Text Aggregator - Comprehensive Report**
```
Module: Text Aggregator
Text: |
  📊 Railway Endpoint Test Report
  ==============================
  
  ✅ Health Check: {{1.status}} 
     Response: {{1.body}}
  
  💰 Account Status: {{2.status}}
     Trading Available: {{2.body.trading_available}}
     Account Info: {{2.body.account_info.retMsg}}
  
  🏠 Root Endpoint: {{3.status}}
     Service: {{3.body.service}}
  
  📚 API Docs: {{4.status}}
     Available at: {{railway_url}}/docs
  
  ⏰ Test Time: {{formatDate(now; "YYYY-MM-DD HH:mm:ss")}}
  
  🔗 Railway URL: {{railway_url}}
```

### **Scenario 3: Trading Decision Testing**

#### **Step 1: Set Variable - Test Payload**
```
Module: Set Variable
Variable Name: test_payload
Value: {
  "ts": "2025-08-19T16:30:00.000000Z",
  "symbol": "SOLUSDT",
  "decision": "skip",
  "allow_new_trades": true,
  "side": "long",
  "confidence": 0.3,
  "reasons": ["low confidence", "testing"],
  "denied_reasons": [],
  "risk_plan": {
    "position_usd": 20.0,
    "max_risk_pct_equity": 0.2,
    "entry_plan": {
      "type": "market",
      "entries": [{"price": 175.0, "size_frac": 1.0}],
      "cancel_if": {"timeout_sec": 3600}
    },
    "stop_loss": 170.0,
    "take_profits": [{"price": 180.0, "close_frac": 1.0}],
    "trail": {}
  },
  "compliance": {"cooldown_min": 45},
  "scores": {"trend_align": 0.3},
  "rr": 1.5
}
```

#### **Step 2: Crypto - Generate HMAC Signature**
```
Module: Crypto → Create a HMAC
Message: {{test_payload}}
Secret: {{your_webhook_secret}}
Algorithm: SHA-256
Output: Hex
```

#### **Step 3: HTTP - Execute Trading Decision**
```
Module: HTTP → Make an HTTP request
Method: POST
URL: {{railway_url}}/v1/execute
Headers:
  Content-Type: application/json
  X-Signature: {{2}}
Body: {{test_payload}}
Timeout: 30 seconds
```

#### **Step 4: Text Aggregator - Trading Test Results**
```
Module: Text Aggregator
Text: |
  🎯 Trading Decision Test Results
  ===============================
  
  Decision: {{test_payload.decision}}
  Symbol: {{test_payload.symbol}}
  Confidence: {{test_payload.confidence}}
  
  Response Status: {{3.status}}
  Trade ID: {{3.body.trade_id}}
  Execution Status: {{3.body.execution_status}}
  
  ⏰ Test Time: {{formatDate(now; "YYYY-MM-DD HH:mm:ss")}}
```

## 🔧 **Make.com Variables Setup**

### **Required Variables:**
```
railway_url = https://your-app-name.up.railway.app
your_webhook_secret = 1e5efa505c87b7583c397fd7d290a827fc783731a30033fe5fe62bbffdedd592
```

## 📋 **Testing Checklist**

### **Basic Endpoints:**
- [ ] Health Check (`/v1/healthz`)
- [ ] Account Status (`/v1/account`)
- [ ] Root Endpoint (`/`)
- [ ] API Documentation (`/docs`)

### **Trading Endpoints:**
- [ ] Execute Decision (`/v1/execute`) - Skip
- [ ] Execute Decision (`/v1/execute`) - Enter (with real trading)

### **Expected Responses:**

#### **Health Check:**
```json
{
  "ok": true,
  "ts": "2025-08-19T16:30:00.000000Z"
}
```

#### **Account Status:**
```json
{
  "trading_available": true,
  "account_info": {
    "retCode": 0,
    "retMsg": "OK",
    "result": { ... }
  }
}
```

#### **Trading Decision (Skip):**
```json
{
  "status": "accepted",
  "trade_id": "uuid-here",
  "decision": "skip",
  "execution_status": "skipped"
}
```

## 🚨 **Troubleshooting**

### **Common Issues:**
1. **Connection Timeout**: Check Railway URL and deployment status
2. **401 Unauthorized**: Verify webhook secret for trading endpoints
3. **500 Internal Error**: Check Railway logs for application errors
4. **Trading Not Available**: Verify Bybit API credentials in Railway environment variables

### **Railway Logs:**
- Go to your Railway project dashboard
- Click on your service
- Check the "Logs" tab for any error messages
