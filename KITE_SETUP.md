# Kite Connect API Setup Guide

Complete guide to connect QuantEdge Pro to Zerodha Kite for live NSE/BSE market data and order execution.

---

## Prerequisites

1. **Zerodha Trading Account** — You need an active Zerodha trading account
2. **Kite Connect Subscription** — ₹2,000/month subscription from [kite.trade/connect](https://kite.trade/connect)
3. **Python 3.11+** — Required for backend

---

## Step 1: Create Kite Connect App

1. Go to [console.zerodha.com](https://console.zerodha.com/)
2. Login with your Zerodha credentials
3. Click **"Create New App"**
4. Fill in the details:
   - **App name**: QuantEdge Pro
   - **Redirect URL**: `http://localhost:3000/kite/callback` (or your domain)
   - **Description**: Institutional quant trading platform
   - **Publisher**: Your name
5. Click **Create**
6. Note down your **API Key** and **API Secret**

---

## Step 2: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install `kiteconnect==4.2.0` and all other dependencies.

---

## Step 3: Configure API Credentials

### Option A: Environment Variables (Recommended for Production)

```bash
export KITE_API_KEY="your_api_key_here"
export KITE_API_SECRET="your_api_secret_here"
```

### Option B: Configuration File (Local Development)

Create `.kite/config.json` in project root:

```json
{
  "api_key": "your_api_key_here",
  "api_secret": "your_api_secret_here",
  "user_id": "AB1234"
}
```

**⚠️ Security**: Add `.kite/` to `.gitignore` to prevent credential leaks!

### Option C: API Endpoint (Dynamic Configuration)

```bash
curl -X POST http://localhost:8000/api/kite/config \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your_api_key",
    "api_secret": "your_api_secret"
  }'
```

---

## Step 4: Authenticate & Get Access Token

Kite uses OAuth 2.0 flow. You need to complete this **once per day** (tokens expire at 6 AM IST).

### 4.1 Start Backend Server

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4.2 Get Login URL

```bash
curl http://localhost:8000/api/kite/auth/login-url
```

Response:
```json
{
  "login_url": "https://kite.zerodha.com/connect/login?api_key=xxx&v=3",
  "instructions": [...]
}
```

### 4.3 Complete Login Flow

1. **Open** the `login_url` in your browser
2. **Login** with your Zerodha credentials (User ID + Password + TOTP)
3. **Authorize** the app
4. You'll be **redirected** to: `http://localhost:3000/kite/callback?request_token=xxxxx&action=login&status=success`
5. **Copy** the `request_token` from the URL

### 4.4 Generate Session

```bash
curl -X POST http://localhost:8000/api/kite/auth/session \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "request_token": "xxx_request_token_from_url_xxx"
  }'
```

Response:
```json
{
  "success": true,
  "access_token": "your_access_token",
  "user_id": "AB1234",
  "user_name": "John Doe",
  "message": "Authentication successful"
}
```

**✅ Done!** Your access token is now saved and valid until 6 AM IST next day.

---

## Step 5: Verify Connection

### Check Auth Status

```bash
curl http://localhost:8000/api/kite/auth/status
```

Expected:
```json
{
  "configured": true,
  "authenticated": true,
  "user_id": "AB1234",
  "api_key": "abcd...xyz"
}
```

### Get Your Profile

```bash
curl http://localhost:8000/api/kite/profile
```

### Get Live Quote

```bash
curl "http://localhost:8000/api/kite/quote?symbols=NSE:INFY,NSE:RELIANCE"
```

### Get Last Traded Price

```bash
curl "http://localhost:8000/api/kite/ltp?symbols=NSE:NIFTY%20BANK,NSE:NIFTY%2050"
```

---

## Step 6: Available Endpoints

### Authentication

- `GET /api/kite/auth/login-url` — Get Kite login URL
- `POST /api/kite/auth/session` — Generate session with request_token
- `GET /api/kite/auth/status` — Check authentication status
- `POST /api/kite/auth/logout` — Invalidate session
- `POST /api/kite/config` — Save API credentials

### Market Data

- `GET /api/kite/quote?symbols=NSE:INFY,NSE:RELIANCE` — Live quotes
- `GET /api/kite/ltp?symbols=NSE:INFY` — Last Traded Price
- `POST /api/kite/historical` — Historical OHLC data
- `GET /api/kite/instruments/{exchange}` — All instruments for exchange
- `GET /api/kite/search?query=INFY&exchange=NSE` — Search instruments

### Order Execution

- `POST /api/kite/order/place` — Place new order
- `DELETE /api/kite/order/{order_id}` — Cancel order
- `GET /api/kite/orders` — Get all orders
- `GET /api/kite/trades` — Get executed trades

### Portfolio

- `GET /api/kite/positions` — Current positions (day + net)
- `GET /api/kite/holdings` — Long-term holdings
- `GET /api/kite/margins` — Account margins
- `GET /api/kite/profile` — User profile

---

## Step 7: Place Your First Order

```bash
curl -X POST http://localhost:8000/api/kite/order/place \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "INFY",
    "exchange": "NSE",
    "transaction_type": "BUY",
    "quantity": 1,
    "order_type": "LIMIT",
    "product": "MIS",
    "price": 1500.0
  }'
```

Response:
```json
{
  "order_id": "240101000000001",
  "status": "success",
  "message": "Order placed successfully: BUY 1 INFY"
}
```

---

## Step 8: Get Historical Data

```bash
curl -X POST http://localhost:8000/api/kite/historical \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "INFY",
    "exchange": "NSE",
    "from_date": "2024-01-01",
    "to_date": "2024-01-31",
    "interval": "day"
  }'
```

Intervals: `minute`, `3minute`, `5minute`, `10minute`, `15minute`, `30minute`, `60minute`, `day`

---

## Frontend Integration

Update `frontend/lib/api.ts` to add Kite API methods:

```typescript
export const kiteAPI = {
  // Auth
  getLoginUrl: () => fetchAPI('/api/kite/auth/login-url'),
  generateSession: (apiKey: string, apiSecret: string, requestToken: string) =>
    fetchAPI('/api/kite/auth/session', {
      method: 'POST',
      body: JSON.stringify({ api_key: apiKey, api_secret: apiSecret, request_token: requestToken }),
    }),
  getAuthStatus: () => fetchAPI('/api/kite/auth/status'),

  // Market Data
  getQuote: (symbols: string) => fetchAPI(`/api/kite/quote?symbols=${symbols}`),
  getLTP: (symbols: string) => fetchAPI(`/api/kite/ltp?symbols=${symbols}`),
  searchInstruments: (query: string, exchange: string = 'NSE') =>
    fetchAPI(`/api/kite/search?query=${query}&exchange=${exchange}`),

  // Orders
  placeOrder: (order: any) =>
    fetchAPI('/api/kite/order/place', { method: 'POST', body: JSON.stringify(order) }),
  getOrders: () => fetchAPI('/api/kite/orders'),

  // Portfolio
  getPositions: () => fetchAPI('/api/kite/positions'),
  getHoldings: () => fetchAPI('/api/kite/holdings'),
  getMargins: () => fetchAPI('/api/kite/margins'),
}
```

---

## WebSocket Streaming (Coming Soon)

Real-time tick-by-tick data via Kite Ticker WebSocket:

```python
from integrations.kite_client import get_kite_client

client = get_kite_client()
ticker = client.create_ticker()

def on_ticks(ws, ticks):
    print("Ticks:", ticks)

ticker.on_ticks = on_ticks
ticker.connect()
ticker.subscribe([256265])  # NIFTY 50 instrument token
ticker.set_mode(ticker.MODE_FULL, [256265])
```

---

## Important Notes

### Rate Limits
- **3 requests/second** — Market data APIs
- **10 requests/second** — Order placement APIs
- Exceeding limits = HTTP 429 (Too Many Requests)

### Access Token
- Valid until **6 AM IST next day**
- Must re-login daily (automate this in production)
- Can be reused across multiple backend instances

### Paper Trading
- Kite doesn't offer paper trading
- Use **mock mode** in QuantEdge Pro for testing strategies
- Test with **1 quantity orders** on real account first

### Security
- **NEVER** commit API keys/secrets to Git
- Use **environment variables** in production
- Enable **2FA** on your Zerodha account
- Monitor **order logs** for unauthorized activity

---

## Troubleshooting

### "kiteconnect not installed"
```bash
pip install kiteconnect==4.2.0
```

### "Kite API not configured"
Set `KITE_API_KEY` and `KITE_API_SECRET` environment variables or use `/api/kite/config` endpoint.

### "Not authenticated"
Complete the login flow to get access_token. Check `/api/kite/auth/status`.

### "Token expired"
Access tokens expire at 6 AM IST. Re-login via `/api/kite/auth/login-url`.

### "Symbol not found"
Use `/api/kite/search?query=RELIANCE` to find exact trading symbol.

### "Insufficient funds"
Check margins: `curl http://localhost:8000/api/kite/margins`

---

## Next Steps

1. ✅ **Setup Complete** — You can now fetch live NSE/BSE data
2. 🔄 **Update Strategies** — Replace mock data with Kite API calls
3. 📊 **WebSocket Streaming** — Add real-time tick data for market making
4. 🤖 **Automate Login** — Create cron job to refresh access_token daily
5. 🚀 **Go Live** — Deploy to production and start algo trading!

---

## Resources

- [Kite Connect Documentation](https://kite.trade/docs/connect/v3/)
- [Kite Connect Python SDK](https://github.com/zerodhatech/pykiteconnect)
- [Zerodha API Console](https://console.zerodha.com/)
- [Zerodha Support](https://support.zerodha.com/)

---

**Ready to trade on live markets! 🚀📈**
