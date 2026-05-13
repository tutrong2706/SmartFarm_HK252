import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import axios from 'axios'

vi.mock('axios')

describe('ReportBuilder', () => {
  beforeEach(() => vi.clearAllMocks())

  it('hiển thị form tạo báo cáo', async () => {
    axios.get.mockResolvedValue({ data: [] })
    const { default: ReportBuilder } = await import('../src/ReportBuilder')

    render(<ReportBuilder />)

    expect(screen.getByLabelText(/Tên báo cáo/i)).toBeTruthy()
    expect(screen.getByLabelText(/Định dạng/i)).toBeTruthy()
    expect(screen.getByLabelText(/Từ ngày/i)).toBeTruthy()
    expect(screen.getByLabelText(/Đến ngày/i)).toBeTruthy()
  })

  it('hiển thị các định dạng CSV/Excel/PDF', async () => {
    axios.get.mockResolvedValue({ data: [] })
    const { default: ReportBuilder } = await import('../src/ReportBuilder')

    render(<ReportBuilder />)

    expect(screen.getByText(/CSV/i)).toBeTruthy()
    expect(screen.getByText(/Excel/i)).toBeTruthy()
    expect(screen.getByText(/PDF/i)).toBeTruthy()
  })

  it('hiển thị nút tạo báo cáo', async () => {
    axios.get.mockResolvedValue({ data: [] })
    const { default: ReportBuilder } = await import('../src/ReportBuilder')

    render(<ReportBuilder />)

    expect(screen.getByText(/Tạo báo cáo/i)).toBeTruthy()
  })
})

describe('ReportHistory', () => {
  beforeEach(() => vi.clearAllMocks())

  it('hiển thị bảng báo cáo rỗng khi chưa có dữ liệu', async () => {
    axios.get.mockResolvedValue({ data: [] })
    const { default: ReportHistory } = await import('../src/ReportHistory')

    render(<ReportHistory />)

    expect(screen.getByText(/Chưa có báo cáo nào/i)).toBeTruthy()
  })

  it('hiển thị danh sách báo cáo khi có dữ liệu', async () => {
    const mockReports = [
      {
        id: 1,
        name: 'Báo cáo tuần 1',
        format: 'csv',
        status: 'completed',
        zone_ids: [1],
        metrics: ['temperature'],
        created_at: new Date().toISOString(),
        file_path: '/reports/test.csv',
        file_size: 1024,
      }
    ]
    axios.get.mockResolvedValue({ data: mockReports })
    const { default: ReportHistory } = await import('../src/ReportHistory')

    render(<ReportHistory />)

    await waitFor(() => {
      expect(screen.getByText(/Báo cáo tuần 1/i)).toBeTruthy()
    })
  })

  it('hiển thị filter trạng thái', async () => {
    axios.get.mockResolvedValue({ data: [] })
    const { default: ReportHistory } = await import('../src/ReportHistory')

    render(<ReportHistory />)

    expect(screen.getByLabelText(/Trạng thái/i)).toBeTruthy()
    expect(screen.getByLabelText(/Định dạng/i)).toBeTruthy()
  })
})