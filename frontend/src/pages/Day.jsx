import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, todayISO } from '../api'
import { ErrorBanner, InsightList, LoadingSpinner, Sentence } from '../components/Common'

const CITY_KEY = 'wardrobe_city'
const SLOT_MARK = { 早晨: '晨', 白天: '昼', 晚上: '夜' }

export default function Day() {
  const [page, setPage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [justWalked] = useState(() => {
    const walked = sessionStorage.getItem('rizhi-just-walked') === '1'
    if (walked) sessionStorage.removeItem('rizhi-just-walked')
    return walked
  })

  const load = () => {
    setLoading(true)
    setError('')
    const city = localStorage.getItem(CITY_KEY) || '北京'
    api.dayPage(todayISO(), city)
      .then(setPage)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const remove = async (id) => {
    try {
      await api.deleteMoment(id)
      load()
    } catch (e) {
      setError(e.message)
    }
  }

  const dateLabel = (() => {
    const d = new Date()
    return `${d.getMonth() + 1}月${d.getDate()}日`
  })()

  return (
    <div className="animate-fade-in pb-8">
      <header className="px-4 pt-6 pb-1">
        <p className="text-soft text-xs mb-0.5">{dateLabel} · 晚上</p>
        <h1 className="font-display text-2xl font-bold tracking-wide">一日页</h1>
      </header>

      {loading && <LoadingSpinner text="在把今天收成一页…" />}
      {error && <ErrorBanner message={error} onRetry={load} />}

      {page && !loading && (
        <>
          <Sentence line={page.glance || page.headline} hint={justWalked ? '今天刚刚走完' : '今天留下的一句'} />

          <p className="mx-5 mt-3 text-[13px] text-soft leading-relaxed">{page.closing}</p>

          <ol className="mx-4 mt-4 flex flex-col gap-3">
            {page.beats.map((beat, i) => (
              <li key={`${beat.slot}-${i}`} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <span className="w-8 h-8 rounded-full bg-ink text-cream text-xs flex items-center justify-center shrink-0">
                    {SLOT_MARK[beat.slot] || beat.slot.slice(0, 1)}
                  </span>
                  {i < page.beats.length - 1 && <span className="w-px flex-1 bg-sand mt-1" />}
                </div>
                <div className="flex-1 pb-2">
                  <p className="text-[11px] text-soft">{beat.slot}</p>
                  <div className="mt-1 p-3.5 rounded-2xl bg-card border border-sand">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-display font-bold text-[15px]">{beat.title}</h3>
                      {beat.moment_id && (
                        <button onClick={() => remove(beat.moment_id)} className="text-[11px] text-soft shrink-0">
                          撤下
                        </button>
                      )}
                    </div>
                    {beat.image_path && (
                      <img src={beat.image_path} alt="" className="mt-2 w-full h-36 object-cover rounded-xl" />
                    )}
                    {beat.edge_hex && (
                      <p className="mt-2 text-[11px] text-soft flex items-center gap-1.5">
                        <span className="w-3 h-3 rounded-full border border-sand" style={{ background: beat.edge_hex }} />
                        端侧主色 {beat.edge_color}
                      </p>
                    )}
                    <p className="text-[13px] leading-relaxed mt-2 text-ink/85">{beat.text}</p>
                    {beat.insights?.length > 0 && (
                      <div className="mt-2">
                        <InsightList items={beat.insights} />
                      </div>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ol>

          <div className="mx-4 mt-2 p-5 rounded-[28px] bg-card border border-sand">
            <p className="text-[10px] tracking-[0.22em] text-soft">明天第一句</p>
            <p className="font-display text-[26px] leading-snug font-bold mt-2">{page.tomorrow}</p>
          </div>

          <div className="mx-4 mt-4 flex gap-4 text-[12px] text-soft">
            <Link to="/" className="underline underline-offset-2">改出门卡</Link>
            <Link to="/snap" className="underline underline-offset-2">再拍一张</Link>
            <Link to="/calendar" className="underline underline-offset-2">穿着记录</Link>
          </div>
        </>
      )}
    </div>
  )
}
