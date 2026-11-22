const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
]

// A stored calendar day, with no meaningful time of day.
// Date-only strings are UTC midnight in JavaScript, so `new Date('2026-09-01')`
// shifts to the previous local day in timezones behind UTC.
const CALENDAR_DATE = /^(\d{4})-(\d{2})-(\d{2})(?:[T\s]00:00:00(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)?$/

export function parseCalendarDate(value) {
  if (value == null || value === '') return null
  const match = String(value).trim().match(CALENDAR_DATE)
  if (!match) return null

  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])
  const utc = new Date(Date.UTC(year, month - 1, day))
  if (
    utc.getUTCFullYear() !== year ||
    utc.getUTCMonth() !== month - 1 ||
    utc.getUTCDate() !== day
  ) {
    return null
  }

  return { year, month, day }
}

/** "2026-09-01" -> "1 September 2026", independent of the browser timezone. */
export function formatCalendarDate(value) {
  const parts = parseCalendarDate(value)
  if (!parts) return ''
  return `${parts.day} ${MONTHS[parts.month - 1]} ${parts.year}`
}

/**
 * Format a real timestamp in the user's timezone.
 * Calendar dates are not passed here; callers use formatStoredDate for those.
 */
export function formatTimestamp(value, { withTime = false } = {}) {
  if (value == null || value === '') return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)

  const formatted = `${date.getDate()} ${MONTHS[date.getMonth()]} ${date.getFullYear()}`
  if (!withTime) return formatted

  const time = date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  })
  return `${formatted}, ${time}`
}

/** Calendar dates stay as stored. Timestamps keep local-timezone formatting. */
export function formatStoredDate(value) {
  if (value == null || value === '') return ''
  return formatCalendarDate(value) || formatTimestamp(value)
}

/** Date string Plotly can place on a UTC axis without moving the calendar day. */
export function toPlotlyCalendarDate(value) {
  const parts = parseCalendarDate(value)
  if (!parts) return value
  const month = String(parts.month).padStart(2, '0')
  const day = String(parts.day).padStart(2, '0')
  return `${parts.year}-${month}-${day}`
}
