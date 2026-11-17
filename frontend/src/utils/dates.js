/**
 * Calendar dates are stored as a day (YYYY-MM-DD), sometimes with a
 * midnight time and no timezone. `new Date("2026-09-01")` reads that as
 * UTC midnight, so toLocaleDateString() can show the previous or next day.
 * Real timestamps (a non-midnight time, or an explicit offset) still follow
 * the user's timezone.
 */

const CALENDAR_DATE = /^(\d{4})-(\d{2})-(\d{2})(?:[T ]00:00(?::00(?:\.0+)?)?)?$/

function calendarDate(year, month, day) {
  const y = Number(year)
  const m = Number(month)
  const d = Number(day)
  const date = new Date(y, m - 1, d)
  if (date.getFullYear() !== y || date.getMonth() !== m - 1 || date.getDate() !== d) {
    return null
  }
  return date
}

export function parseStoredDate(value) {
  if (value == null || value === '') return null
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value

  const text = String(value).trim()
  const calendarMatch = text.match(CALENDAR_DATE)
  if (calendarMatch) {
    return calendarDate(calendarMatch[1], calendarMatch[2], calendarMatch[3])
  }

  const normalized = text.includes(' ') && !text.includes('T') ? text.replace(' ', 'T') : text
  const parsed = new Date(normalized)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

export function formatStoredDate(value, options) {
  if (value == null || value === '') return ''
  const date = parseStoredDate(value)
  if (!date) return String(value)
  return date.toLocaleDateString('en-US', options)
}

export function formatStoredDateTime(value, options) {
  if (value == null || value === '') return ''
  const date = parseStoredDate(value)
  if (!date) return String(value)
  return date.toLocaleString('en-US', options)
}
