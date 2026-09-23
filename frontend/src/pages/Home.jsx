import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, todayISO } from '../api'
import { glanceLine } from '../glance'
import { LoadingSpinner, ErrorBanner, Tag, AIBadge, EmptyState, Sentence } from '../components/Common'

const OCCASIONS = ['日常上课', '约会', '运动健身', '面试答辩', '周末出游', '聚会派对']
const CITY_KEY = 'wardrobe_city'

export default function Home() {
  const navigate = useNavigate()
  const [city, setCity] = useState(() => localStorage.getItem(CITY_KEY) || '北京')
  const [weather, setWeather] = useState(null)
  const [occasion, setOccasion] = useState('日常上课')
  const [result, setResult] = useState(null)
  const [current, setCurrent] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [cityEditing, setCityEditing] = useState(false)
  const [clothesCount, setClothesCount] = useState(0)
  const [idleCount, setIdleCount] = useState(0)
  const [booted, setBooted] = useState(false)
  const [walking, setWalking] = useState(false)

  const today = new Date()
  const dateStr = `${today.getMonth() + 1}月${today.getDate()}日`
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

  const generate = useCallback(async (occ, cityName) => {
    setLoading(true)
    setError('')
    setSaved(false)
    try {
      const data = await api.recommend(occ, cityName)
      setResult(data)
      setWeather(data.weather || null)
      setCurrent(0)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancel = false
    ;(async () => {
      setError('')
      try {
        const [w, clothes, outfits] = await Promise.all([
          api.getWeather(city),
          api.listClothes(),
          api.listOutfits(todayISO().slice(0, 7)),
        ])
        if (cancel) return
        setWeather(w)
        setClothesCount(clothes.items.length)
        setIdleCount(clothes.items.filter((c) => !c.wear_count).length)
        const savedOutfit = (outfits.items || []).find((o) => o.date === todayISO())
        if (savedOutfit && clothes.items.length >= 2) {
          const dep = await api.departure(city, savedOutfit.occasion || '日常上课', savedOutfit.title || '')
          if (cancel) return
          setOccasion(savedOutfit.occasion || '日常上课')
          setWeather(dep.weather || w)
          setResult({
            outfits: [savedOutfit],
            brings: dep.brings,
            weather: dep.weather || w,
            ai_powered: false,
          })
          setCurrent(0)
          setSaved(true)
        } else if (clothes.items.length >= 2) {
          setSaved(false)
          setLoading(true)
          const data = await api.recommend(occasion, city)
          if (cancel) return
          setResult(data)
          setWeather(data.weather || w)
          setCurrent(0)
        }
      } catch (e) {
        if (!cancel) setError(e.message)
      } finally {
        if (!cancel) {
          setLoading(false)
          setBooted(true)
        }
      }
    })()
    return () => { cancel = true }
    // 只在城市变化时重载；场合切换走 switchOccasion
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [city])

  const switchOccasion = (occ) => {
    setOccasion(occ)
    generate(occ, city)
  }

  const confirmWear = async () => {
    const outfit = result?.outfits?.[current]
    if (!outfit) return
    try {
      await api.saveOutfit({
        date: todayISO(),
        occasion,
        item_ids: outfit.item_ids,
        title: outfit.title,
        reasoning: outfit.reasoning,
        weather: result.weather || weather || {},
      })
      setSaved(true)
    } catch (e) {
      setError(e.message)
    }
  }

  const walkDay = async () => {
    setWalking(true)
    setError('')
    try {
      await api.rehearse(city, occasion)
      sessionStorage.setItem('rizhi-just-walked', '1')
      navigate('/day')
    } catch (e) {
      setError(e.message)
      setWalking(false)
    }
  }

  const outfit = result?.outfits?.[current]
  const brings = result?.brings || []
  const line = outfit ? glanceLine(brings, occasion, outfit.title) : ''
  const hour = today.getHours()
  const dayPart = hour < 12 ? '上午' : hour < 18 ? '下午' : '晚上'
  const knows = []
  if (weather) {
    const temp = Math.round(weather.temperature)
    knows.push(temp >= 28
      ? `${temp}°C ${weather.description}，厚衣服今天不上身`
      : `${temp}°C ${weather.description}，${weather.advice}`)
  }
  knows.push(`${weekdays[today.getDay()]}${dayPart}，先按「${occasion}」准备`)
  if (clothesCount) {
    knows.push(idleCount
      ? `衣橱 ${clothesCount} 件，还有 ${idleCount} 件没上过身`
      : `衣橱 ${clothesCount} 件，只从已经有的里面选`)
  }

  return (
    <div className="animate-fade-in pb-4">
      <header className="px-4 pt-6 pb-1 flex items-start justify-between">
        <div>
          <p className="text-soft text-xs mb-0.5">
            {dateStr} · {weekdays[today.getDay()]}
          </p>
          <h1 className="font-display text-2xl font-bold tracking-wide">
            <Link to="/about" className="hover:text-accent">日知</Link>
            <span className="text-soft font-normal text-base ml-2">今天出门</span>
          </h1>
        </div>
        <button
          onClick={() => setCityEditing(!cityEditing)}
          className="flex items-center gap-1 px-3 py-1.5 rounded-full bg-card border border-sand text-sm text-soft active:scale-95 transition-transform"
        >
          {city}
        </button>
      </header>

      {cityEditing && (
        <div className="mx-4 mb-2 p-3 rounded-xl bg-card shadow-soft flex gap-2 animate-fade-in">
          <input
            autoFocus
            defaultValue={city}
            placeholder="输入城市，如：杭州"
            className="flex-1 bg-cream rounded-lg px-3 py-2 text-sm outline-none"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.target.value.trim()) {
                const c = e.target.value.trim()
                setCity(c)
                localStorage.setItem(CITY_KEY, c)
                setCityEditing(false)
              }
            }}
          />
          <button
            className="px-4 py-2 rounded-lg bg-ink text-cream text-sm font-semibold"
            onClick={(e) => {
              const input = e.target.previousSibling
              if (input.value.trim()) {
                setCity(input.value.trim())
                localStorage.setItem(CITY_KEY, input.value.trim())
                setCityEditing(false)
              }
            }}
          >
            确定
          </button>
        </div>
      )}

      <Sentence line={line} />

      {knows.length > 0 && (
        <ul className="mx-4 mt-4 flex flex-col gap-1.5">
          {knows.map((text) => (
            <li key={text} className="text-[13px] leading-snug text-ink/80 pl-3 border-l-2 border-accent/70">
              {text}
            </li>
          ))}
        </ul>
      )}

      <div className="flex gap-2 px-4 mt-4 overflow-x-auto no-scrollbar pb-1">
        {OCCASIONS.map((occ) => (
          <Tag key={occ} active={occ === occasion} onClick={() => switchOccasion(occ)}>
            {occ}
          </Tag>
        ))}
      </div>

      <div className="flex items-end justify-between px-4 mt-5 mb-3">
        <h2 className="font-display text-lg font-bold tracking-wide">出门卡</h2>
        {result && <AIBadge powered={result.ai_powered} />}
      </div>

      {error && <ErrorBanner message={error} onRetry={() => generate(occasion, city)} />}

      {!booted && !error ? (
        <LoadingSpinner text="正在看今天的天气和衣橱…" />
      ) : clothesCount < 2 && !loading ? (
        <EmptyState
          icon="👕"
          title="衣橱还太少"
          desc="先录入两件衣服，出门卡才能从你已有的衣服里选"
          action={
            <button
              onClick={() => navigate('/upload')}
              className="px-6 py-2.5 rounded-full bg-accent text-white font-semibold text-sm shadow-soft active:scale-95 transition-transform"
            >
              去录入 →
            </button>
          }
        />
      ) : loading ? (
        <LoadingSpinner text="正在拼今天这套…" />
      ) : outfit ? (
        <div className="px-4 animate-fade-up" key={current + occasion + (saved ? 'saved' : 'new')}>
          <div className="bg-card rounded-2xl shadow-soft overflow-hidden">
            <div className="px-4 pt-4 flex items-center justify-between">
              <h3 className="font-display text-lg font-bold">{outfit.title}</h3>
              <span className="text-xs text-soft">
                {saved ? '今天已定' : `${current + 1} / ${result.outfits.length}`}
              </span>
            </div>

            <div className="flex gap-2.5 px-4 py-3.5 overflow-x-auto no-scrollbar">
              {(outfit.items || []).map((item) => (
                <div key={item.id} className="shrink-0 w-24">
                  <div className="w-24 h-24 rounded-xl bg-cream overflow-hidden border border-sand">
                    {item.image_path ? (
                      <img src={item.image_path} alt={item.name} className="img-item" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-2xl">👕</div>
                    )}
                  </div>
                  <p className="text-[11px] mt-1.5 text-center leading-tight line-clamp-2">{item.name}</p>
                  <p className="text-[10px] text-soft text-center">{item.category}</p>
                </div>
              ))}
            </div>

            <div className="mx-4 mb-3 p-3.5 rounded-xl bg-cream/80 border border-sand">
              <p className="text-[13px] leading-relaxed text-ink/85">{outfit.reasoning}</p>
              {outfit.tip && (
                <p className="text-xs text-accent mt-2">{outfit.tip}</p>
              )}
            </div>

            {brings.length > 0 && (
              <div className="px-4 pb-3">
                <p className="text-[11px] text-soft mb-2 tracking-wide">出门带上</p>
                <div className="flex flex-col gap-1.5">
                  {brings.map((b) => (
                    <div key={b.label} className="flex items-baseline gap-2 text-[13px]">
                      <span className="shrink-0 px-2 py-0.5 rounded-full bg-ink text-cream text-[11px]">{b.label}</span>
                      <span className="text-ink/75">{b.why}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-2.5 px-4 pb-4">
              {!saved && result.outfits.length > 1 && (
                <button
                  onClick={() => setCurrent((current + 1) % result.outfits.length)}
                  className="flex-1 py-3 rounded-xl border border-sand bg-card font-semibold text-sm active:scale-[0.98] transition-transform"
                >
                  换一套
                </button>
              )}
              {saved && (
                <button
                  onClick={() => generate(occasion, city)}
                  className="flex-1 py-3 rounded-xl border border-sand bg-card font-semibold text-sm active:scale-[0.98] transition-transform"
                >
                  重新搭配
                </button>
              )}
              <button
                onClick={saved ? () => navigate('/day') : confirmWear}
                className={`flex-1 py-3 rounded-xl font-semibold text-sm shadow-soft active:scale-[0.98] transition-all ${
                  saved ? 'bg-sage text-white' : 'bg-accent text-white'
                }`}
              >
                {saved ? '去看一日页' : '今天就穿这套'}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <button
        onClick={walkDay}
        disabled={walking || clothesCount < 2}
        className="mx-4 mt-4 w-[calc(100%-2rem)] text-left rounded-2xl bg-ink text-cream px-4 py-4 active:scale-[0.99] transition-transform disabled:opacity-60"
      >
        <span className="font-display text-lg font-bold">{walking ? '正在把今天走完' : '走完今天'}</span>
        <span className="block text-[12px] text-cream/65 mt-1 leading-relaxed">
          按现在的天气重写出门，补上门口那一眼，直接翻到晚上
        </span>
      </button>

      <div className="grid grid-cols-2 gap-2.5 mx-4 mt-4">
        <Link to="/snap" className="p-3.5 rounded-2xl bg-card border border-sand active:scale-[0.99] transition-transform">
          <p className="font-display font-bold text-sm">随手一拍</p>
          <p className="text-[11px] text-soft mt-1 leading-relaxed">衣柜、书包、桌面或门口</p>
        </Link>
        <Link to="/day" className="p-3.5 rounded-2xl bg-card border border-sand active:scale-[0.99] transition-transform">
          <p className="font-display font-bold text-sm">晚间一日页</p>
          <p className="text-[11px] text-soft mt-1 leading-relaxed">只记今天真正发生的</p>
        </Link>
      </div>

      <div className="mx-4 mt-3 flex gap-4 text-[12px] text-soft">
        <Link to="/diagnosis" className="underline underline-offset-2">衣橱里有什么</Link>
        <Link to="/calendar" className="underline underline-offset-2">穿着记录</Link>
        <Link to="/about" className="underline underline-offset-2">赛道说明</Link>
      </div>
    </div>
  )
}
