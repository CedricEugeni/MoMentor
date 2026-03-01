import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { CurrencyPreference, getCurrencyPreference } from "@/lib/currency"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

interface CurrencyFormatOptions {
  currency?: CurrencyPreference
  fxRateToUsd?: number
  minimumFractionDigits?: number
  maximumFractionDigits?: number
}

export function convertFromUsd(valueUsd: number, currency: CurrencyPreference, fxRateToUsd: number = 1): number {
  if (currency === "USD") {
    return valueUsd
  }

  if (!Number.isFinite(fxRateToUsd) || fxRateToUsd <= 0) {
    return valueUsd
  }

  return valueUsd / fxRateToUsd
}

export function formatCurrency(valueUsd: number, options?: CurrencyFormatOptions): string {
  const currency = options?.currency ?? getCurrencyPreference()
  const fxRateToUsd = options?.fxRateToUsd ?? 1
  const convertedValue = convertFromUsd(valueUsd, currency, fxRateToUsd)
  const locale = currency === "EUR" ? "fr-FR" : "en-US"

  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: options?.minimumFractionDigits ?? 2,
    maximumFractionDigits: options?.maximumFractionDigits ?? 2,
  }).format(convertedValue)
}

export function formatShares(value: number): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 4,
  }).format(value)
}

export function formatPercent(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
