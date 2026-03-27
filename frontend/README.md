# QuantEdge Pro - Frontend

Modern Next.js 14 frontend for the Quantitative Finance Platform targeting Indian stock market.

## 🚀 Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS + Custom Dark Theme
- **Charts**: Recharts
- **Icons**: Lucide React
- **State**: Zustand (for global state)
- **API Client**: Axios

## 📦 Installation

```bash
cd frontend
npm install
```

## 🛠️ Development

```bash
# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 🎨 Features

- ✅ **Dashboard** - Portfolio overview with real-time metrics
- ✅ **Portfolio Analytics** - Holdings, tax analysis (LTCG/STCG)
- ⏳ **Options Analytics** - Greeks, IV analysis, options chain
- ⏳ **Strategy Builder** - Options strategies with payoff diagrams
- ⏳ **Algo Trading** - Automated strategy monitoring
- ⏳ **Risk Management** - Pre-trade checks and compliance
- ⏳ **Backtesting** - Historical strategy testing
- ⏳ **AI Models** - ML model management

## 🌐 Deployment to Vercel

### Step 1: Push to GitHub

```bash
cd /home/user/Invvest
git add frontend/
git commit -m "Add Next.js frontend"
git push origin claude/quant-finance-portfolio-tool-fAcoy
```

### Step 2: Deploy to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### Step 3: Environment Variables

Add in Vercel Dashboard → Settings → Environment Variables:

```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### Step 4: Deploy

Click "Deploy" and wait for build to complete!

## 📁 Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with sidebar
│   ├── page.tsx           # Dashboard page
│   ├── globals.css        # Global styles
│   ├── portfolio/         # Portfolio analytics page
│   ├── options/           # Options analytics page
│   ├── strategy/          # Strategy builder page
│   └── algo/              # Algo trading page
├── components/            # Reusable components
│   ├── Sidebar.tsx        # Navigation sidebar
│   ├── Header.tsx         # Top header with market data
│   └── ui/                # UI components
│       └── MetricCard.tsx
├── lib/                   # Utilities
│   └── utils.ts           # Helper functions
├── types/                 # TypeScript types
│   └── index.ts
├── public/                # Static assets
├── package.json
├── tailwind.config.ts     # TailwindCSS config
├── tsconfig.json          # TypeScript config
└── next.config.js         # Next.js config
```

## 🎨 Design System

### Colors

- **Background**: `#0a0e27` (dark-900)
- **Cards**: `#0f1429` (dark-800)
- **Primary**: `#8b5cf6` (purple-500)
- **Success**: `#10b981`
- **Danger**: `#ef4444`
- **Warning**: `#f59e0b`

### Components

- Cards use `card-glass` utility class for glassmorphism effect
- All metrics display with trend indicators
- Charts use gradient fills for visual appeal
- Dark theme optimized for financial data

## 🔗 API Integration

The frontend connects to the FastAPI backend via `NEXT_PUBLIC_API_URL`.

Example API call:

```typescript
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL

export async function getPortfolio() {
  const response = await axios.get(`${API_URL}/api/portfolio`)
  return response.data
}
```

## 📱 Pages Overview

### Dashboard (`/`)
- Portfolio value and today's P&L
- Performance chart vs Nifty 50
- Sector allocation pie chart
- Risk summary with VaR
- Open positions table
- AI market regime indicator

### Portfolio Analytics (`/portfolio`)
- Holdings with STCG/LTCG tax calculations
- Risk-adjusted metrics (Sharpe, Sortino, Calmar)
- Monthly returns chart
- Correlation analysis

### Options Analytics (`/options`)
- Real-time Greeks (Delta, Gamma, Theta, Vega, Rho)
- Options chain for NSE stocks
- Implied volatility skew
- Put-call parity validation
- 3D volatility surface

### Strategy Builder (`/strategy`)
- Pre-built strategy templates
- Custom strategy leg builder
- Payoff diagram visualization
- Greeks neutral optimization
- Indian market expiry calendar

### Algo Trading (`/algo`)
- Active strategy cards
- Intraday performance chart
- Technical indicators dashboard
- Execution timeline
- Market microstructure insights

## 🚨 Notes

- This is the MVP with Dashboard completed
- Additional pages need to be built based on your design screenshots
- Backend API needs to be deployed separately (FastAPI on Railway/Render)
- Add authentication before production deployment

## 📄 License

Proprietary - QuantEdge Pro Platform
