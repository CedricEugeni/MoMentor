export type ThemePreference = "system" | "light" | "dark"

const THEME_STORAGE_KEY = "momentor_theme_preference"

export const getThemePreference = (): ThemePreference => {
  if (typeof window === "undefined") {
    return "system"
  }

  const stored = window.localStorage.getItem(THEME_STORAGE_KEY)
  if (stored === "light" || stored === "dark" || stored === "system") {
    return stored
  }

  return "system"
}

export const applyTheme = (preference: ThemePreference): void => {
  if (typeof window === "undefined") {
    return
  }

  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches
  const isDark = preference === "dark" || (preference === "system" && prefersDark)

  document.documentElement.classList.toggle("dark", isDark)
}

export const setThemePreference = (preference: ThemePreference): void => {
  if (typeof window === "undefined") {
    return
  }

  window.localStorage.setItem(THEME_STORAGE_KEY, preference)
  applyTheme(preference)
  window.dispatchEvent(new CustomEvent("momentor-theme-change"))
}
