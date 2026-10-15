import { ApiError, api, ENDPOINTS, json } from './api'

/**
 * Exchange a Google Identity Services ID token for a Kinship session. Django sets the
 * httpOnly auth cookies; the `tokens` in the JSON body are for the Android app and ignored here.
 */
export async function loginWithGoogle(idToken: string) {
  await api(ENDPOINTS.googleAuth, json('POST', { id_token: idToken }))
}

export async function logout() {
  await api(ENDPOINTS.logout, json('POST', {})).catch((e) => {
    if (!(e instanceof ApiError)) throw e
  })
}

export const isAuthError = (e: unknown) =>
  e instanceof ApiError && (e.status === 401 || e.status === 403)

let gsiPromise: Promise<void> | null = null
export function loadGoogleScript(): Promise<void> {
  gsiPromise ??= new Promise((resolve, reject) => {
    const s = document.createElement('script')
    s.src = 'https://accounts.google.com/gsi/client'
    s.async = true
    s.onload = () => resolve()
    s.onerror = () => reject(new Error('Could not load Google Identity Services'))
    document.head.appendChild(s)
  })
  return gsiPromise
}
