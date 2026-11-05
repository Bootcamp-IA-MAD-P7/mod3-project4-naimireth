const API_BASE = import.meta.env.VITE_API_URL || '/api'

export function apiAssetUrl(path) {
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path
  const base = API_BASE.replace(/\/$/, '')
  return path.startsWith('/') ? `${base}${path}` : `${base}/${path}`
}

async function request(path, options = {}) {
  const { headers, ...rest } = options
  const response = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: { Accept: 'application/json', ...(headers || {}) },
  })

  if (!response.ok) {
    let detail = `Error ${response.status}`
    try {
      const payload = await response.json()
      detail = payload.detail || detail
    } catch {
      // El backend no devolvio JSON; se mantiene el mensaje generico.
    }
    throw new Error(detail)
  }

  return response.json()
}

export function uploadVideo(file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_BASE}/analyses`)
    xhr.responseType = 'json'

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100))
      }
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(xhr.response)
        return
      }
      const detail = xhr.response?.detail || `Error ${xhr.status}`
      reject(new Error(detail))
    }

    xhr.onerror = () => reject(new Error('No se pudo conectar con el backend'))
    xhr.ontimeout = () => reject(new Error('La subida del video ha caducado'))

    const formData = new FormData()
    formData.append('file', file)
    xhr.send(formData)
  })
}

export const api = {
  health: () => request('/health'),
  dashboard: () => request('/dashboard'),
  analyses: (limit = 100) => request(`/analyses?limit=${limit}`),
  analysis: (id) => request(`/analyses/${id}`),
  progress: (id) => request(`/analyses/${id}/progress`),
  preview: (id) => request(`/analyses/${id}/preview`),
}
