import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface AlgorithmRun {
  id: number
  run_date: string
  trigger_type: 'auto' | 'manual' | 'test'
  total_capital_usd: number
  input_currency: 'USD' | 'EUR'
  fx_rate_to_usd: number
  fx_rate_timestamp_utc: string | null
  status: 'pending' | 'completed'
  created_at: string
}

export interface Recommendation {
  symbol: string
  target_percentage: number
  target_amount_usd: number
}

export interface CashflowMove {
  symbol: string
  action: 'SELL' | 'BUY'
  suggested_shares: number
  suggested_value_usd: number
  order_index: number
}

export interface SwapMove {
  from_symbol: string | null
  to_symbol: string | null
  swap_shares_from: number | null
  swap_shares_to: number | null
  swap_value_usd: number
  order_index: number
  description: string
}

export interface ActualPosition {
  symbol: string
  actual_shares: number
  actual_avg_price_usd: number
  total_value_usd: number
  first_validation_date: string
}

export interface RunDetails extends AlgorithmRun {
  uninvested_cash_usd: number
  allocation_residual_cash_usd: number
  recommendations: Recommendation[]
  cashflow_moves: CashflowMove[]
  swap_moves: SwapMove[]
  actual_positions: ActualPosition[] | null
  actual_cash: number | null
}

export interface PortfolioPosition {
  symbol: string
  shares: number
  entry_price: number
  current_price: number
  entry_value: number
  current_value: number
  pnl_usd: number
  pnl_percent: number
}

export interface Portfolio {
  has_portfolio: boolean
  run_id?: number
  run_date?: string
  validation_date?: string
  positions?: PortfolioPosition[]
  uninvested_cash?: number
  total_entry_value?: number
  total_current_value?: number
  total_pnl_usd?: number
  total_pnl_percent?: number
  fx_rate_to_usd?: number
  fx_rate_timestamp_utc?: string
  message?: string
  error?: string
}

// API calls
export const generateRun = async (mode: string, capital?: number, capitalCurrency: 'USD' | 'EUR' = 'USD') => {
  const response = await api.post<{ run_id: number }>('/api/runs/generate', {
    mode,
    capital,
    capital_currency: capitalCurrency,
  })
  return response.data
}

export const hasPendingRuns = async () => {
  const response = await api.get<{ has_pending: boolean }>('/api/runs/has-pending')
  return response.data
}

export const listRuns = async () => {
  const response = await api.get<{ runs: AlgorithmRun[] }>('/api/runs')
  return response.data
}

export const getRunDetails = async (runId: number) => {
  const response = await api.get<RunDetails>(`/api/runs/${runId}/details`)
  return response.data
}

export const confirmPositions = async (
  runId: number,
  positions: { symbol: string; shares: number; avg_price: number }[],
  uninvestedCash: number,
  forceConfirm: boolean = false
) => {
  const response = await api.post(`/api/runs/${runId}/confirm-positions`, {
    positions,
    uninvested_cash: uninvestedCash,
    force_confirm: forceConfirm,
  })
  return response.data
}

export const getCurrentPortfolio = async () => {
  const response = await api.get<Portfolio>('/api/portfolio/current')
  return response.data
}

export const resetDatabase = async () => {
  const response = await api.post('/api/reset')
  return response.data
}
