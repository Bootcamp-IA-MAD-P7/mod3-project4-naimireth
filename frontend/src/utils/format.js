export function formatDuration(seconds) {
  if (seconds === null || seconds === undefined || Number.isNaN(Number(seconds))) {
    return '—'
  }

  const total = Math.max(0, Math.round(Number(seconds)))
  const hours = Math.floor(total / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  const remaining = total % 60
  const body = `${String(minutes).padStart(2, '0')}:${String(remaining).padStart(2, '0')}`

  return hours > 0 ? `${hours}:${body}` : body
}

export function formatSeconds(seconds) {
  if (seconds === null || seconds === undefined || Number.isNaN(Number(seconds))) {
    return '—'
  }
  return `${Number(seconds).toFixed(1)} s`
}

export function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '—'
  }
  return `${Number(value).toFixed(1)}%`
}

export function formatNumber(value) {
  return new Intl.NumberFormat('es-ES').format(Number(value || 0))
}

export function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / 1024 ** exponent
  return `${value.toFixed(value >= 10 || exponent === 0 ? 0 : 1)} ${units[exponent]}`
}

export function formatDate(value) {
  if (!value) return '—'
  const normalized =
    typeof value === 'string' && !/[zZ]$|[+-]\d{2}:\d{2}$/.test(value) ? `${value}Z` : value
  const date = new Date(normalized)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function statusLabel(status) {
  const labels = {
    queued: 'En cola',
    processing: 'Procesando',
    completed: 'Completado',
    failed: 'Error',
  }
  return labels[status] || status || 'Desconocido'
}

export function brandColor(name) {
  const palette = {
    Adidas: '#4ade80',
    Emirates: '#a3e635',
    Nike: '#facc15',
    Spotify: '#2dd4bf',
  }
  return palette[name] || '#22c55e'
}
