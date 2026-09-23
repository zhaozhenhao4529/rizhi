import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, todayISO } from '../api'
import { AIBadge, ErrorBanner, InsightList } from '../components/Common'

const SCENES = [
  { id: '衣柜', hint: '哪些还没穿' },
  { id: '书包', hint: '今天该带什么' },
  { id: '桌面', hint: '和今天的关系' },
  { id: '门口', hint: '锁门前对一下' },
]
const CITY_KEY = 'wardrobe_city'

export default function Snap() {
  const fileRef = useRef(null)
  const [scene, setScene] = useState('衣柜')
  const [preview, setPreview] = useState('')
  const [reading, setReading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const onFile = async (file) => {
    if (!file) return
    setError('')
    setSaved(false)
    setResult(null)
    setPreview(URL.createObjectURL(file))
    setReading(true)
    try {
      const city = localStorage.getItem(CITY_KEY) || '北京'
      const data = await api.understandMoment(file, scene, city)
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setReading(false)
    }
  }

  const save = async () => {
    if (!result) return
    setSaving(true)
    setError('')
    try {
      await api.saveMoment({
        date: todayISO(),
        scene: result.scene || scene,
        image_path: result.temp_image || '',
        summary: result.summary || '',
        insights: result.insights || [],
        edge_color: result.edge_color || '',
        edge_hex: result.edge_hex || '',
        ai_powered: !!result.ai_powered,
      })
      setSaved(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="animate-fade-in pb-6">
      <header className="px-4 pt-6 pb-2">
        <p className="text-soft text-xs mb-0.5">白天</p>
        <h1 className="font-display text-2xl font-bold tracking-wide">随手一拍</h1>
        <p className="text-soft text-xs mt-1 leading-relaxed">
          手机当眼睛。端侧先取主色，再对照你已有的衣橱和今天的天气。
        </p>
      </header>

      <div className="grid grid-cols-4 gap-2 px-4 mt-3">
        {SCENES.map((s) => (
          <button
            key={s.id}
            onClick={() => setScene(s.id)}
            className={`rounded-2xl px-1 py-2.5 text-center border transition-all active:scale-95 ${
              scene === s.id ? 'bg-ink text-cream border-ink' : 'bg-card text-ink border-sand'
            }`}
          >
            <span className="block text-sm font-semibold">{s.id}</span>
            <span className={`block text-[10px] mt-0.5 leading-tight ${scene === s.id ? 'text-cream/70' : 'text-soft'}`}>
              {s.hint}
            </span>
          </button>
        ))}
      </div>

      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        className="sr-only"
        onChange={(e) => onFile(e.target.files?.[0])}
      />

      <button
        onClick={() => fileRef.current?.click()}
        className="mx-4 mt-4 w-[calc(100%-2rem)] aspect-[4/3] rounded-3xl border border-dashed border-sand bg-card overflow-hidden flex items-center justify-center active:scale-[0.99] transition-transform"
      >
        {preview ? (
          <img src={preview} alt="这一拍" className="w-full h-full object-cover" />
        ) : (
          <div className="text-center px-8">
            <p className="font-display text-lg font-bold">拍{scene}</p>
            <p className="text-soft text-xs mt-1">用相机，或从相册选一张</p>
          </div>
        )}
      </button>

      {error && <div className="mt-3"><ErrorBanner message={error} /></div>}

      {reading && (
        <p className="text-center text-sm text-soft mt-4">正在读这一眼…</p>
      )}

      {result && !reading && (
        <div className="mx-4 mt-4 rounded-2xl bg-card shadow-soft animate-fade-up overflow-hidden">
          <div className="h-16" style={{ background: result.edge_hex || '#e8dcc4' }} />
          <div className="p-4 -mt-6">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span
                className="w-10 h-10 rounded-full border-2 border-white shadow-soft"
                style={{ background: result.edge_hex || '#e8dcc4' }}
                title={result.edge_color}
              />
              <div>
                <p className="text-[11px] text-soft">端侧主色</p>
                <p className="text-sm font-semibold">{result.edge_color}</p>
              </div>
            </div>
            <AIBadge powered={result.ai_powered} />
          </div>
          <p className="text-[14px] leading-relaxed">{result.summary}</p>
          <div className="mt-3">
            <InsightList items={result.insights} />
          </div>
          <button
            onClick={save}
            disabled={saving || saved}
            className={`mt-4 w-full py-3 rounded-xl font-semibold text-sm shadow-soft active:scale-[0.98] transition-all ${
              saved ? 'bg-sage text-white' : 'bg-accent text-white'
            }`}
          >
            {saved ? '已记进今天' : saving ? '记下…' : '记进今天'}
          </button>
          {saved && (
            <Link to="/day" className="block text-center text-sm text-accent mt-3">
              去晚间一日页看这一拍 →
            </Link>
          )}
          </div>
        </div>
      )}
    </div>
  )
}
