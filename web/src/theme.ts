import { useCallback, useState } from 'react'

export type Theme = 'light' | 'dark'

const read = (): Theme =>
  document.documentElement.dataset.theme === 'light' ? 'light' : 'dark'

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(read)
  const toggle = useCallback(() => {
    const next: Theme = read() === 'light' ? 'dark' : 'light'
    document.documentElement.dataset.theme = next
    try {
      localStorage.setItem('kinship-theme', next)
    } catch {
      // Private mode etc: the theme still applies for this visit.
    }
    setTheme(next)
  }, [])
  return { theme, toggle }
}
