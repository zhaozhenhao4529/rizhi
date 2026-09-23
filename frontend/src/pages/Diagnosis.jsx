import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { LoadingSpinner, AIBadge, EmptyState } from '../components/Common'

const PRIORITY_STYLE = {
  高: 'bg-red-100 text-red-600',
  中: 'bg-amber-100 text-amber-600',
  低: 'bg-sage/20 text-sage',
}

export default function Diagnosis() {
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const run = () => {
    setLoading(true)
    setError('')
    api.diagnose()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(run, [])

  return (
    <div className="animate-fade-in pb-8">
      <header className="px-4 pt-6 pb-3">
        <h1 className="font-display text-2xl font-bold tracking-wide">衣橱里有什么</h1>
        <p className="text-soft text-xs mt-1">先看你已经拥有的，再标出今天用不上的缺口</p>
      </header>

      {loading && <LoadingSpinner text="AI 顾问分析中…" />}

      {error && !loading && (
        <EmptyState
          icon="🧺"
          title="暂时无法诊断"
          desc={error}
          action={
            <button
              onClick={() => navigate('/upload')}
              className="px-6 py-2.5 rounded-full bg-accent text-white font-semibold text-sm shadow-soft"
            >
              去录入衣物 →
            </button>
          }
        />
      )}

      {data && !loading && (
        <div className="px-4 space-y-4 animate-fade-up">
          {/* 总体诊断 */}
          <div className="bg-gradient-to-br from-ink to-[#4a423b] rounded-2xl p-4 text-cream shadow-lift">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-display font-bold">📋 总体诊断</h3>
              <AIBadge powered={data.ai_powered} />
            </div>
            <p className="text-[13px] leading-relaxed text-cream/90">{data.summary}</p>
          </div>

          {/* 优势 */}
          {data.strengths?.length > 0 && (
            <div className="bg-card rounded-2xl shadow-soft p-4">
              <h3 className="font-display font-bold mb-2.5">💪 衣橱优势</h3>
              <div className="space-y-2">
                {data.strengths.map((s, i) => (
                  <div key={i} className="flex items-start gap-2 text-[13px] text-ink/85">
                    <span className="text-sage font-bold shrink-0">✓</span>
                    <span>{s}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 缺口 + 购买建议 */}
          {data.gaps?.length > 0 && (
            <div className="bg-card rounded-2xl shadow-soft p-4">
              <h3 className="font-display font-bold mb-1">🧩 衣橱缺口</h3>
              <p className="text-[11px] text-soft mb-3">补齐这些单品，搭配自由度大幅提升</p>
              <div className="space-y-3">
                {data.gaps.map((g, i) => (
                  <div key={i} className="p-3.5 rounded-xl bg-cream border border-sand">
                    <div className="flex items-center justify-between mb-1.5">
                      <h4 className="font-semibold text-sm">{g.missing}</h4>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${PRIORITY_STYLE[g.priority] || PRIORITY_STYLE.低}`}>
                        {g.priority}优先级
                      </span>
                    </div>
                    <p className="text-xs text-soft leading-relaxed mb-2.5">{g.reason}</p>
                    <a
                      href={`https://s.taobao.com/search?q=${encodeURIComponent(g.search_keyword)}`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-accent text-white text-xs font-semibold active:scale-95 transition-transform"
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-3.5 h-3.5">
                        <circle cx="11" cy="11" r="7" />
                        <path d="m20 20-3.5-3.5" strokeLinecap="round" />
                      </svg>
                      去天猫搜「{g.search_keyword}」
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 购买原则 */}
          {data.advice && (
            <div className="bg-sage/10 border border-sage/30 rounded-2xl p-4">
              <h3 className="font-display font-bold mb-1.5 text-sage">💡 购买原则</h3>
              <p className="text-[13px] text-ink/80 leading-relaxed">{data.advice}</p>
            </div>
          )}

          <button
            onClick={run}
            className="w-full py-3 rounded-xl border border-sand bg-card font-semibold text-sm active:scale-[0.99] transition-transform"
          >
            🔄 重新诊断
          </button>
        </div>
      )}
    </div>
  )
}
