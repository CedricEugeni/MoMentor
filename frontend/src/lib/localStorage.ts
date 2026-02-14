const LOCAL_STORAGE_KEY_PREFIX = 'momentor_pending_confirmation_'
const EXPIRATION_DAYS = 14

interface PendingConfirmation {
  runId: number
  positions: { symbol: string; shares: number; avg_price: number }[]
  uninvestedCash: number
  timestamp: number
}

export const savePendingConfirmation = (
  runId: number,
  positions: { symbol: string; shares: number; avg_price: number }[],
  uninvestedCash: number
) => {
  const data: PendingConfirmation = {
    runId,
    positions,
    uninvestedCash,
    timestamp: Date.now(),
  }
  localStorage.setItem(`${LOCAL_STORAGE_KEY_PREFIX}${runId}`, JSON.stringify(data))
}

export const getPendingConfirmation = (runId: number): PendingConfirmation | null => {
  const stored = localStorage.getItem(`${LOCAL_STORAGE_KEY_PREFIX}${runId}`)
  if (!stored) return null

  try {
    const data: PendingConfirmation = JSON.parse(stored)
    
    // Check if expired
    const age = Date.now() - data.timestamp
    const maxAge = EXPIRATION_DAYS * 24 * 60 * 60 * 1000
    
    if (age > maxAge) {
      // Expired, remove it
      localStorage.removeItem(`${LOCAL_STORAGE_KEY_PREFIX}${runId}`)
      return null
    }
    
    return data
  } catch {
    return null
  }
}

export const removePendingConfirmation = (runId: number) => {
  localStorage.removeItem(`${LOCAL_STORAGE_KEY_PREFIX}${runId}`)
}

export const cleanupExpiredConfirmations = () => {
  const maxAge = EXPIRATION_DAYS * 24 * 60 * 60 * 1000
  const now = Date.now()
  
  // Iterate through all localStorage keys
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(LOCAL_STORAGE_KEY_PREFIX)) {
      try {
        const data = JSON.parse(localStorage.getItem(key) || '{}')
        if (data.timestamp && now - data.timestamp > maxAge) {
          localStorage.removeItem(key)
        }
      } catch {
        // Invalid data, remove it
        localStorage.removeItem(key)
      }
    }
  }
}

export const clearAllPendingConfirmations = () => {
  // Remove all MoMentor localStorage entries
  const keysToRemove: string[] = []
  
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(LOCAL_STORAGE_KEY_PREFIX)) {
      keysToRemove.push(key)
    }
  }
  
  keysToRemove.forEach(key => localStorage.removeItem(key))
}
