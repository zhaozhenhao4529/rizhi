import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { LoadingSpinner, ErrorBanner, Tag, EmptyState } from '../components/Common'

const CATEGORIES = ['全部', '上装', '下装', '外套', '连衣裙', '鞋子', '配饰']
const CATEGORY_ICONS = { 上装: '👕', 下装: '👖', 外套: '🧥', 连衣裙: '👗', 鞋子: '👟', 配饰: '👜' }

export default function Wardrobe() {
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [category, setCategory] = useState('全部')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [detail, setDetail] = useState(null)

  const load = () => {
    setLoading(true)
    api.listClothes()
      .then((d) => setItems(d.items))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const filtered = useMemo(
    () => (category === '全部' ? items : items.filter((i) => i.category === category)),
    [items, category]
  )

  const stats = useMemo(() => {
    const s = {}
    items.forEach((i) => { s[i.category] = (s[i.category] || 0) + 1 })
    return s
  }, [items])

  const remove = async (id) => {
    try {
      await api.deleteClothing(id)
      setDetail(null)
      load()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="animate-fade-in">
      <header className="px-4 pt-6 pb-3">
        <h1 className="font-display text-2xl font-bold tracking-wide">我的衣橱</h1>
        <p className="text-soft text-xs mt-1">
          共 {items.length} 件单品
          {Object.entries(stats).map(([k, v]) => (
            <span key={k} className="ml-2">{CATEGORY_ICONS[k]} {v}</span>
          ))}
        </p>
      </header>

      <div className="flex gap-2 px-4 overflow-x-auto no-scrollbar pb-2">
        {CATEGORIES.map((c) => (
          <Tag key={c} active={c === category} onClick={() => setCategory(c)}>
            {c !== '全部' && CATEGORY_ICONS[c]} {c}
          </Tag>
        ))}
      </div>

      {error && <ErrorBanner message={error} onRetry={load} />}
      {loading ? (
        <LoadingSpinner />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon="🧺"
          title={category === '全部' ? '衣橱空空如也' : `还没有${category}`}
          desc="拍张照，AI 自动识别录入"
          action={
            <button
              onClick={() => navigate('/upload')}
              className="px-6 py-2.5 rounded-full bg-accent text-white font-semibold text-sm shadow-soft active:scale-95 transition-transform"
            >
              去录入 →
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-3 gap-2.5 px-4 pb-4">
          {filtered.map((item, idx) => (
            <button
              key={item.id}
              onClick={() => setDetail(item)}
              className="bg-card rounded-xl overflow-hidden shadow-soft text-left active:scale-[0.97] transition-transform animate-fade-up"
              style={{ animationDelay: `${Math.min(idx * 40, 300)}ms` }}
            >
              <div className="aspect-square bg-cream">
                {item.image_path ? (
                  <img src={item.image_path} alt={item.name} className="img-item" loading="lazy" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-3xl">
                    {CATEGORY_ICONS[item.category] || '👕'}
                  </div>
                )}
              </div>
              <div className="p-2">
                <p className="text-xs font-medium leading-tight line-clamp-1">{item.name}</p>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-[10px] text-soft">{item.subcategory || item.category}</span>
                  {item.wear_count > 0 && (
                    <span className="text-[10px] text-accent">穿过{item.wear_count}次</span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* 详情弹层 */}
      {detail && (
        <div
          className="fixed inset-0 z-[60] bg-ink/40 backdrop-blur-sm flex items-end justify-center"
          onClick={() => setDetail(null)}
        >
          <div
            className="w-full max-w-[430px] bg-cream rounded-t-3xl p-5 pb-8 animate-fade-up"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="w-10 h-1 rounded-full bg-sand mx-auto mb-4" />
            <div className="flex gap-4">
              <div className="w-28 h-28 rounded-2xl bg-card overflow-hidden border border-sand shrink-0">
                {detail.image_path ? (
                  <img src={detail.image_path} alt={detail.name} className="img-item" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-4xl">
                    {CATEGORY_ICONS[detail.category] || '👕'}
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-display text-lg font-bold leading-snug">{detail.name}</h3>
                <p className="text-soft text-xs mt-0.5">
                  {detail.category} · {detail.subcategory}
                </p>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {detail.colors.map((c) => (
                    <span key={c} className="px-2 py-0.5 rounded-full bg-card border border-sand text-[11px]">{c}</span>
                  ))}
                  {detail.style_tags.map((t) => (
                    <span key={t} className="px-2 py-0.5 rounded-full bg-accent/10 text-accent text-[11px]">{t}</span>
                  ))}
                </div>
              </div>
            </div>

            {detail.description && (
              <p className="mt-4 p-3 rounded-xl bg-card text-[13px] text-ink/80 leading-relaxed border border-sand">
                {detail.description}
              </p>
            )}

            <div className="grid grid-cols-2 gap-3 mt-4 text-center">
              <div className="p-3 rounded-xl bg-card border border-sand">
                <p className="text-[11px] text-soft mb-1">保暖度</p>
                <p className="text-sm font-semibold">{'🔥'.repeat(detail.warmth_level)}</p>
              </div>
              <div className="p-3 rounded-xl bg-card border border-sand">
                <p className="text-[11px] text-soft mb-1">正式度</p>
                <p className="text-sm font-semibold">{'⭐'.repeat(detail.formality)}</p>
              </div>
            </div>

            <div className="flex gap-2.5 mt-5">
              <button
                onClick={() => setDetail(null)}
                className="flex-1 py-3 rounded-xl border border-sand bg-card font-semibold text-sm"
              >
                关闭
              </button>
              <button
                onClick={() => remove(detail.id)}
                className="flex-1 py-3 rounded-xl bg-red-500 text-white font-semibold text-sm active:scale-[0.98] transition-transform"
              >
                删除这件
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
