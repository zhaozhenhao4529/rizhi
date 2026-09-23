import { useState, useEffect, useMemo } from 'react'
import { api, todayISO } from '../api'
import { LoadingSpinner, SectionTitle } from '../components/Common'

export default function Calendar() {
  const now = new Date()
  const [year, setYear] = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth()) // 0-based
  const [outfits, setOutfits] = useState([])
  const [stats, setStats] = useState(null)
  const [selected, setSelected] = useState(now.toISOString().slice(0, 10))
  const [loading, setLoading] = useState(true)

  const monthStr = `${year}-${String(month + 1).padStart(2, '0')}`

  useEffect(() => {
    setLoading(true)
    Promise.all([api.listOutfits(monthStr), api.outfitStats(monthStr)])
      .then(([o, s]) => {
        setOutfits(o.items)
        setStats(s)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [monthStr])

  const byDate = useMemo(() => {
    const map = {}
    outfits.forEach((o) => {
      if (!map[o.date]) map[o.date] = []
      map[o.date].push(o)
    })
    return map
  }, [outfits])

  // 构建月历格子
  const cells = useMemo(() => {
    const first = new Date(year, month, 1)
    const daysInMonth = new Date(year, month + 1, 0).getDate()
    const offset = first.getDay()
    const arr = []
    for (let i = 0; i < offset; i++) arr.push(null)
    for (let d = 1; d <= daysInMonth; d++) arr.push(d)
    return arr
  }, [year, month])

  const prevMonth = () => {
    if (month === 0) { setYear(year - 1); setMonth(11) } else setMonth(month - 1)
  }
  const nextMonth = () => {
    if (month === 11) { setYear(year + 1); setMonth(0) } else setMonth(month + 1)
  }

  const selectedOutfits = byDate[selected] || []
  const todayStr = todayISO()

  return (
    <div className="animate-fade-in">
      <header className="px-4 pt-6 pb-3">
        <h1 className="font-display text-2xl font-bold tracking-wide">穿着记录</h1>
        <p className="text-soft text-xs mt-1">确认过的每一套，都会写进那一天的一日页</p>
      </header>

      {/* 月度统计 */}
      {stats && (
        <div className="grid grid-cols-3 gap-2.5 px-4 mb-4">
          <StatCard label="记录穿搭" value={stats.total_outfits} unit="套" />
          <StatCard label="活跃天数" value={stats.active_days} unit="天" />
          <StatCard label="衣橱单品" value={stats.total_clothes} unit="件" />
        </div>
      )}

      {/* 月历 */}
      <div className="mx-4 bg-card rounded-2xl shadow-soft p-4">
        <div className="flex items-center justify-between mb-3">
          <button onClick={prevMonth} className="w-8 h-8 rounded-full bg-cream text-soft active:scale-90 transition-transform">‹</button>
          <h3 className="font-display font-bold">{year}年{month + 1}月</h3>
          <button onClick={nextMonth} className="w-8 h-8 rounded-full bg-cream text-soft active:scale-90 transition-transform">›</button>
        </div>
        <div className="grid grid-cols-7 gap-1 text-center text-[11px] text-soft mb-1.5">
          {['日', '一', '二', '三', '四', '五', '六'].map((d) => <div key={d}>{d}</div>)}
        </div>
        <div className="grid grid-cols-7 gap-1">
          {cells.map((d, i) => {
            if (d === null) return <div key={`e${i}`} />
            const dateStr = `${monthStr}-${String(d).padStart(2, '0')}`
            const has = byDate[dateStr]?.length > 0
            const isSelected = dateStr === selected
            const isToday = dateStr === todayStr
            return (
              <button
                key={dateStr}
                onClick={() => setSelected(dateStr)}
                className={`aspect-square rounded-xl text-sm flex flex-col items-center justify-center relative transition-all active:scale-90 ${
                  isSelected ? 'bg-accent text-white font-bold shadow-soft'
                  : isToday ? 'bg-accent/10 text-accent font-semibold'
                  : 'text-ink/80'
                }`}
              >
                {d}
                {has && !isSelected && (
                  <span className="absolute bottom-1 w-1.5 h-1.5 rounded-full bg-sage" />
                )}
                {has && isSelected && (
                  <span className="absolute bottom-1 w-1.5 h-1.5 rounded-full bg-white" />
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* 选中日期的穿搭 */}
      <SectionTitle>{selected.slice(5).replace('-', '月')}日 的穿搭</SectionTitle>
      {loading ? (
        <LoadingSpinner />
      ) : selectedOutfits.length === 0 ? (
        <p className="text-center text-soft text-sm py-8">这一天还没有穿搭记录</p>
      ) : (
        <div className="px-4 space-y-3 pb-6">
          {selectedOutfits.map((o) => (
            <div key={o.id} className="bg-card rounded-2xl shadow-soft p-4 animate-fade-up">
              <div className="flex items-center justify-between mb-2.5">
                <h4 className="font-display font-bold text-[15px]">{o.title || '当日穿搭'}</h4>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-sand text-soft">{o.occasion}</span>
              </div>
              <div className="flex gap-2 overflow-x-auto no-scrollbar">
                {o.items.map((item) => (
                  <div key={item.id} className="shrink-0 w-16">
                    <div className="w-16 h-16 rounded-lg bg-cream overflow-hidden border border-sand">
                      {item.image_path && <img src={item.image_path} alt={item.name} className="img-item" />}
                    </div>
                    <p className="text-[10px] mt-1 text-center line-clamp-1">{item.name}</p>
                  </div>
                ))}
              </div>
              {o.reasoning && (
                <p className="text-xs text-soft mt-2.5 leading-relaxed">{o.reasoning}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 最常穿 */}
      {stats?.top_items?.length > 0 && (
        <>
          <SectionTitle>本月最常穿</SectionTitle>
          <div className="flex gap-2.5 px-4 overflow-x-auto no-scrollbar pb-6">
            {stats.top_items.map((item, idx) => (
              <div key={item.id} className="shrink-0 w-24 bg-card rounded-xl shadow-soft overflow-hidden">
                <div className="relative w-24 h-24 bg-cream">
                  {item.image_path && <img src={item.image_path} alt={item.name} className="img-item" />}
                  <span className="absolute top-1 left-1 w-5 h-5 rounded-full bg-ink text-cream text-[10px] font-bold flex items-center justify-center">
                    {idx + 1}
                  </span>
                </div>
                <div className="p-1.5 text-center">
                  <p className="text-[11px] line-clamp-1">{item.name}</p>
                  <p className="text-[10px] text-accent">穿过 {item.wear_count} 次</p>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function StatCard({ label, value, unit }) {
  return (
    <div className="bg-card rounded-xl shadow-soft p-3 text-center">
      <p className="text-xl font-bold font-display">
        {value}
        <span className="text-xs font-normal text-soft ml-0.5">{unit}</span>
      </p>
      <p className="text-[11px] text-soft mt-0.5">{label}</p>
    </div>
  )
}
