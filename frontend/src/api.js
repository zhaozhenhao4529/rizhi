const BASE = ''

async function request(path, options = {}) {
  const resp = await fetch(`${BASE}${path}`, {
    headers: options.body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!resp.ok) {
    let msg = `请求失败 (${resp.status})`
    try {
      const data = await resp.json()
      msg = data.detail || msg
    } catch {}
    throw new Error(msg)
  }
  return resp.json()
}

export function todayISO(d = new Date()) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export const api = {
  health: () => request('/api/health'),
  getWeather: (city) => request(`/api/weather?city=${encodeURIComponent(city)}`),
  listClothes: (category) =>
    request(`/api/clothes${category && category !== '全部' ? `?category=${encodeURIComponent(category)}` : ''}`),
  recognize: (file) => {
    const fd = new FormData()
    fd.append('image', file)
    return request('/api/clothes/recognize', { method: 'POST', body: fd })
  },
  saveClothing: (item) => request('/api/clothes', { method: 'POST', body: JSON.stringify(item) }),
  deleteClothing: (id) => request(`/api/clothes/${id}`, { method: 'DELETE' }),
  recommend: (occasion, city) =>
    request('/api/recommend', { method: 'POST', body: JSON.stringify({ occasion, city }) }),
  saveOutfit: (payload) => request('/api/outfits', { method: 'POST', body: JSON.stringify(payload) }),
  listOutfits: (month) => request(`/api/outfits${month ? `?month=${month}` : ''}`),
  outfitStats: (month) => request(`/api/outfits/stats${month ? `?month=${month}` : ''}`),
  diagnose: () => request('/api/wardrobe/diagnosis', { method: 'POST' }),
  departure: (city, occasion, title) =>
    request(`/api/departure?city=${encodeURIComponent(city)}&occasion=${encodeURIComponent(occasion)}&title=${encodeURIComponent(title || '')}`),
  understandMoment: (file, scene, city) => {
    const fd = new FormData()
    fd.append('image', file)
    fd.append('scene', scene)
    fd.append('city', city)
    return request('/api/moments/understand', { method: 'POST', body: fd })
  },
  saveMoment: (payload) => request('/api/moments', { method: 'POST', body: JSON.stringify(payload) }),
  deleteMoment: (id) => request(`/api/moments/${id}`, { method: 'DELETE' }),
  dayPage: (date, city) =>
    request(`/api/day?date=${encodeURIComponent(date || '')}&city=${encodeURIComponent(city || '北京')}`),
  rehearse: (city, occasion) =>
    request(`/api/day/rehearse?city=${encodeURIComponent(city)}&occasion=${encodeURIComponent(occasion)}`, { method: 'POST' }),
}
