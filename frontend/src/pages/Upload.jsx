import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { AIBadge } from '../components/Common'

const CATEGORIES = ['上装', '下装', '外套', '连衣裙', '鞋子', '配饰']
const COLORS = ['白', '黑', '灰', '米', '驼', '牛仔蓝', '浅蓝', '藏青', '粉', '红', '绿', '黄', '焦糖', '奶茶', '碎花']
const STYLES = ['休闲', '正式', '运动', '街头', '甜美', '简约', '复古', '学院']
const SEASONS = ['春', '夏', '秋', '冬']

export default function Upload() {
  const navigate = useNavigate()
  const fileRef = useRef(null)
  const [preview, setPreview] = useState('')
  const [tempImage, setTempImage] = useState('')
  const [recognizing, setRecognizing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [aiPowered, setAiPowered] = useState(null)
  const [error, setError] = useState('')
  const [form, setForm] = useState(null)

  const onFile = async (file) => {
    if (!file) return
    setError('')
    setPreview(URL.createObjectURL(file))
    setRecognizing(true)
    setForm(null)
    try {
      const result = await api.recognize(file)
      setForm(result)
      setTempImage(result.temp_image)
      setAiPowered(result.ai_powered)
    } catch (e) {
      setError(e.message)
      setPreview('')
    } finally {
      setRecognizing(false)
    }
  }

  const toggleList = (key, value) => {
    setForm((f) => {
      const list = f[key].includes(value) ? f[key].filter((v) => v !== value) : [...f[key], value]
      return { ...f, [key]: list }
    })
  }

  const save = async () => {
    if (!form?.name?.trim()) {
      setError('给衣物起个名字吧')
      return
    }
    setSaving(true)
    setError('')
    try {
      await api.saveClothing({ ...form, image_path: tempImage })
      navigate('/wardrobe')
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="animate-fade-in pb-8">
      <header className="px-4 pt-6 pb-3">
        <h1 className="font-display text-2xl font-bold tracking-wide">录入衣物</h1>
        <p className="text-soft text-xs mt-1">拍张照，AI 自动识别品类、颜色、风格</p>
      </header>

      {/* 拍照/上传区 */}
      <div className="px-4">
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => onFile(e.target.files?.[0])}
        />
        {!preview ? (
          <button
            onClick={() => fileRef.current?.click()}
            className="w-full aspect-[4/3] rounded-2xl border-2 border-dashed border-accent/40 bg-card flex flex-col items-center justify-center gap-3 active:scale-[0.99] transition-transform"
          >
            <div className="w-16 h-16 rounded-full bg-accent/10 flex items-center justify-center text-3xl">
              📸
            </div>
            <div className="text-center">
              <p className="font-semibold text-sm">拍照或从相册选择</p>
              <p className="text-soft text-xs mt-1">建议平铺拍摄，背景简洁识别更准</p>
            </div>
          </button>
        ) : (
          <div className="relative rounded-2xl overflow-hidden bg-card shadow-soft">
            <img src={preview} alt="预览" className="w-full aspect-[4/3] object-cover" />
            {recognizing && (
              <div className="absolute inset-0 bg-ink/50 backdrop-blur-[2px] flex flex-col items-center justify-center gap-3">
                <div className="w-12 h-12 rounded-full border-[3px] border-white/30 border-t-white animate-spin" />
                <p className="text-white text-sm font-medium">AI 识别中…</p>
              </div>
            )}
            {!recognizing && (
              <button
                onClick={() => { setPreview(''); setForm(null); setAiPowered(null) }}
                className="absolute top-3 right-3 w-8 h-8 rounded-full bg-ink/60 text-white text-sm flex items-center justify-center"
              >
                ✕
              </button>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="mx-4 mt-3 p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* 识别结果表单 */}
      {form && !recognizing && (
        <div className="px-4 mt-5 space-y-5 animate-fade-up">
          <div className="flex items-center justify-between">
            <h2 className="font-display font-bold">识别结果 · 可修改</h2>
            <AIBadge powered={aiPowered} />
          </div>

          {/* 名称 */}
          <div>
            <label className="text-xs text-soft block mb-1.5">名称</label>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-4 py-3 rounded-xl bg-card border border-sand text-sm outline-none focus:border-accent transition-colors"
              placeholder="如：奶白色针织开衫"
            />
          </div>

          {/* 品类 */}
          <div>
            <label className="text-xs text-soft block mb-1.5">品类</label>
            <div className="flex flex-wrap gap-2">
              {CATEGORIES.map((c) => (
                <Chip key={c} active={form.category === c} onClick={() => setForm({ ...form, category: c })}>
                  {c}
                </Chip>
              ))}
            </div>
          </div>

          {/* 颜色 */}
          <div>
            <label className="text-xs text-soft block mb-1.5">颜色（可多选）</label>
            <div className="flex flex-wrap gap-2">
              {COLORS.map((c) => (
                <Chip key={c} active={form.colors.includes(c)} onClick={() => toggleList('colors', c)}>
                  {c}
                </Chip>
              ))}
            </div>
          </div>

          {/* 风格 */}
          <div>
            <label className="text-xs text-soft block mb-1.5">风格（可多选）</label>
            <div className="flex flex-wrap gap-2">
              {STYLES.map((s) => (
                <Chip key={s} active={form.style_tags.includes(s)} onClick={() => toggleList('style_tags', s)}>
                  {s}
                </Chip>
              ))}
            </div>
          </div>

          {/* 季节 */}
          <div>
            <label className="text-xs text-soft block mb-1.5">适合季节（可多选）</label>
            <div className="flex flex-wrap gap-2">
              {SEASONS.map((s) => (
                <Chip key={s} active={form.season.includes(s)} onClick={() => toggleList('season', s)}>
                  {s}
                </Chip>
              ))}
            </div>
          </div>

          {/* 保暖度 / 正式度 */}
          <div className="grid grid-cols-2 gap-4">
            <LevelPicker
              label="保暖度"
              value={form.warmth_level}
              onChange={(v) => setForm({ ...form, warmth_level: v })}
              icon="🔥"
            />
            <LevelPicker
              label="正式度"
              value={form.formality}
              onChange={(v) => setForm({ ...form, formality: v })}
              icon="⭐"
            />
          </div>

          <button
            onClick={save}
            disabled={saving}
            className="w-full py-3.5 rounded-xl bg-accent text-white font-bold shadow-lift active:scale-[0.99] transition-all disabled:opacity-60"
          >
            {saving ? '保存中…' : '✓ 收进衣橱'}
          </button>
        </div>
      )}
    </div>
  )
}

function Chip({ children, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`px-3.5 py-1.5 rounded-full text-[13px] transition-all active:scale-95 ${
        active ? 'bg-accent text-white font-semibold shadow-soft' : 'bg-card text-soft border border-sand'
      }`}
    >
      {children}
    </button>
  )
}

function LevelPicker({ label, value, onChange, icon }) {
  return (
    <div className="p-3 rounded-xl bg-card border border-sand">
      <p className="text-xs text-soft mb-2">{label}</p>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((v) => (
          <button
            key={v}
            onClick={() => onChange(v)}
            className={`flex-1 h-7 rounded-md text-[10px] transition-all ${
              v <= value ? 'bg-accent/15' : 'bg-cream'
            }`}
          >
            {v <= value ? icon : ''}
          </button>
        ))}
      </div>
    </div>
  )
}
