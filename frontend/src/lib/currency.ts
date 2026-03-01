import { useEffect, useState } from "react"

export type CurrencyPreference = "USD" | "EUR"

const CURRENCY_STORAGE_KEY = "momentor_currency_preference"
export const CURRENCY_CHANGE_EVENT = "momentor-currency-change"

export const getCurrencyPreference = (): CurrencyPreference => {
  if (typeof window === "undefined") {
    return "USD"
  }

  const stored = window.localStorage.getItem(CURRENCY_STORAGE_KEY)
  if (stored === "USD" || stored === "EUR") {
    return stored
  }

  return "USD"
}

export const setCurrencyPreference = (currency: CurrencyPreference): void => {
  if (typeof window === "undefined") {
    return
  }

  window.localStorage.setItem(CURRENCY_STORAGE_KEY, currency)
  window.dispatchEvent(new CustomEvent(CURRENCY_CHANGE_EVENT, { detail: currency }))
}

export const useCurrencyPreference = () => {
  const [currency, setCurrencyState] = useState<CurrencyPreference>(getCurrencyPreference())

  useEffect(() => {
    const handleCurrencyChange = () => setCurrencyState(getCurrencyPreference())

    window.addEventListener(CURRENCY_CHANGE_EVENT, handleCurrencyChange)
    return () => window.removeEventListener(CURRENCY_CHANGE_EVENT, handleCurrencyChange)
  }, [])

  const setCurrency = (value: CurrencyPreference) => {
    setCurrencyState(value)
    setCurrencyPreference(value)
  }

  return { currency, setCurrency }
}
