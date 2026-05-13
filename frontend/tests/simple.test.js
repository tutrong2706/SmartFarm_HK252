import { describe, it, expect } from 'vitest'

describe('Simple tests', () => {
  it('true is true', () => {
    expect(true).toBe(true)
  })

  it('parseJwt basic', () => {
    const parseJwt = (token) => {
      try { return JSON.parse(atob(token.split('.')[1])) } catch { return null }
    }
    expect(parseJwt('invalid')).toBeNull()
    const payload = { sub: 'test', role: 'ADMIN' }
    const token = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.${btoa(JSON.stringify(payload))}.sig`
    expect(parseJwt(token)).toEqual(payload)
  })
})