import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { formatDate, formatDateOnly, formatTime, formatDuration } from './date'

describe('date utils', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('formatDate', () => {
    it('should format date string correctly', () => {
      const result = formatDate('2024-03-15T10:30:45.000Z')
      expect(result).toMatch(/2024-03-15 \d{2}:\d{2}:\d{2}/)
    })

    it('should return dash for empty string', () => {
      expect(formatDate('')).toBe('-')
    })

    it('should return dash for undefined', () => {
      expect(formatDate(undefined)).toBe('-')
    })

    it('should return dash for invalid date', () => {
      expect(formatDate('invalid-date')).toBe('-')
    })

    it('should handle ISO date string', () => {
      const result = formatDate('2024-01-01T00:00:00Z')
      expect(result).toMatch(/2024-01-01/)
    })
  })

  describe('formatDateOnly', () => {
    it('should format date only correctly', () => {
      const result = formatDateOnly('2024-03-15T10:30:45.000Z')
      expect(result).toBe('2024-03-15')
    })

    it('should return dash for empty string', () => {
      expect(formatDateOnly('')).toBe('-')
    })

    it('should return dash for undefined', () => {
      expect(formatDateOnly(undefined)).toBe('-')
    })

    it('should return dash for invalid date', () => {
      expect(formatDateOnly('not-a-date')).toBe('-')
    })
  })

  describe('formatTime', () => {
    it('should return dash for empty string', () => {
      expect(formatTime('')).toBe('-')
    })

    it('should return dash for invalid date', () => {
      expect(formatTime('invalid')).toBe('-')
    })

    it('should return "刚刚" for recent time', () => {
      const now = new Date('2024-03-15T10:00:00Z')
      vi.setSystemTime(now)

      const justNow = new Date(now.getTime() - 30 * 1000).toISOString()
      expect(formatTime(justNow)).toBe('刚刚')
    })

    it('should return minutes ago for recent minutes', () => {
      const now = new Date('2024-03-15T10:00:00Z')
      vi.setSystemTime(now)

      const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000).toISOString()
      expect(formatTime(fiveMinutesAgo)).toBe('5分钟前')
    })

    it('should return hours ago for recent hours', () => {
      const now = new Date('2024-03-15T10:00:00Z')
      vi.setSystemTime(now)

      const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString()
      expect(formatTime(twoHoursAgo)).toBe('2小时前')
    })

    it('should return days ago for recent days', () => {
      const now = new Date('2024-03-15T10:00:00Z')
      vi.setSystemTime(now)

      const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString()
      expect(formatTime(threeDaysAgo)).toBe('3天前')
    })

    it('should return date only for old dates', () => {
      const now = new Date('2024-03-15T10:00:00Z')
      vi.setSystemTime(now)

      const oldDate = new Date(now.getTime() - 40 * 24 * 60 * 60 * 1000).toISOString()
      expect(formatTime(oldDate)).toMatch(/\d{4}-\d{2}-\d{2}/)
    })
  })

  describe('formatDuration', () => {
    it('should format milliseconds', () => {
      expect(formatDuration(500)).toBe('500ms')
    })

    it('should format seconds', () => {
      expect(formatDuration(1500)).toBe('1.5s')
    })

    it('should format seconds without decimal', () => {
      expect(formatDuration(2000)).toBe('2.0s')
    })

    it('should format minutes and seconds', () => {
      expect(formatDuration(65000)).toBe('1m 5s')
    })

    it('should format minutes only', () => {
      expect(formatDuration(60000)).toBe('1m 0s')
    })

    it('should handle zero', () => {
      expect(formatDuration(0)).toBe('0ms')
    })
  })
})
