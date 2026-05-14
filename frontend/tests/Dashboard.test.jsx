import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { BrowserRouter } from 'react-router-dom'
import axios from 'axios'

vi.mock('axios')

describe('Utils', () => {
  it('parseJwt trả về null cho token không hợp lệ', () => {
    const parseJwt = (token) => {
      try { return JSON.parse(atob(token.split('.')[1])) } catch { return null }
    }
    expect(parseJwt('invalid')).toBeNull()
    expect(parseJwt('')).toBeNull()
  })

  it('parseJwt giải mã token hợp lệ', () => {
    const parseJwt = (token) => {
      try { return JSON.parse(atob(token.split('.')[1])) } catch { return null }
    }
    const payload = { sub: 'testuser', name: 'Test User', role: 'ADMIN' }
    const token = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.${btoa(JSON.stringify(payload))}.signature`
    expect(parseJwt(token)).toEqual(payload)
  })
})

describe('Dashboard smoke test', () => {
  it('render mà không crash', async () => {
    axios.get.mockResolvedValue({ data: [] })
    const { default: Dashboard } = await import('../src/Dashboard')

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    expect(screen.getByText(/Bảng điều khiển/i)).toBeTruthy()
    expect(screen.getByText(/Tổng khu vực/i)).toBeTruthy()
    expect(screen.getByText(/Dashboard Động/i)).toBeTruthy()
  })
})

describe('Report smoke test', () => {
  it('ReportBuilder render heading', async () => {
    axios.get.mockResolvedValue({ data: [] })
    const { default: ReportBuilder } = await import('../src/ReportBuilder')

    render(<ReportBuilder />)
    expect(screen.getByText(/BẢO CÁO/i)).toBeTruthy()
  })

  it('ReportHistory render heading', async () => {
    axios.get.mockResolvedValue({ data: [] })
    const { default: ReportHistory } = await import('../src/ReportHistory')

    render(<ReportHistory />)
    expect(screen.getByText(/LỊCH SỬ BÁO CÁO/i)).toBeTruthy()
  })
})