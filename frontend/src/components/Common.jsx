/** 通用小组件 */

export function LoadingSpinner({ text = '加载中…' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <div className="w-10 h-10 rounded-full border-[3px] border-sand border-t-accent animate-spin" />
      <p className="text-soft text-sm">{text}</p>
    </div>
  )
}

export function EmptyState({ icon = '🧺', title, desc, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-8 text-center animate-fade-in">
      <div className="text-5xl mb-4">{icon}</div>
      <h3 className="font-display text-lg font-bold mb-1">{title}</h3>
      <p className="text-soft text-sm mb-5">{desc}</p>
      {action}
    </div>
  )
}

export function ErrorBanner({ message, onRetry }) {
  return (
    <div className="mx-4 my-3 p-3.5 rounded-xl bg-red-50 border border-red-200 flex items-center gap-3 animate-fade-in">
      <span className="text-lg">⚠️</span>
      <p className="text-sm text-red-700 flex-1">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="text-xs font-semibold text-red-600 underline shrink-0">
          重试
        </button>
      )}
    </div>
  )
}

export function Tag({ children, active = false, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`px-3.5 py-1.5 rounded-full text-[13px] whitespace-nowrap transition-all active:scale-95 ${
        active
          ? 'bg-ink text-cream font-semibold shadow-soft'
          : 'bg-card text-soft border border-sand'
      }`}
    >
      {children}
    </button>
  )
}

export function SectionTitle({ children, extra }) {
  return (
    <div className="flex items-end justify-between px-4 mt-6 mb-3">
      <h2 className="font-display text-lg font-bold tracking-wide">{children}</h2>
      {extra}
    </div>
  )
}

export function Sentence({ line, hint = '腕上只留这一句' }) {
  const parts = (line || '').split(' · ').map((s) => s.trim()).filter(Boolean)
  return (
    <div className="mx-4 mt-4 rounded-[28px] bg-ink text-cream px-5 pt-5 pb-6 shadow-lift">
      <div className="flex items-center justify-between">
        <p className="text-[10px] tracking-[0.22em] text-cream/45">{hint}</p>
        <span className="w-11 h-11 rounded-full border border-cream/20 flex items-center justify-center text-[10px] tracking-[0.18em]">
          日知
        </span>
      </div>
      <div className="mt-4">
        {parts.length ? parts.map((part, i) => (
          <p
            key={`${part}-${i}`}
            className="sentence-line font-display text-[40px] leading-[1.12] font-bold"
            style={{ animationDelay: `${i * 90}ms` }}
          >
            {part}
          </p>
        )) : (
          <p className="font-display text-2xl text-cream/35">正在看今天</p>
        )}
      </div>
    </div>
  )
}

export function Glance({ line, hint = '腕上 · 一句话' }) {
  return (
    <div className="mx-4 mt-3 flex items-center gap-3 px-3 py-3 rounded-2xl bg-ink text-cream shadow-lift">
      <div className="w-14 h-14 rounded-full border border-cream/25 flex items-center justify-center shrink-0">
        <div className="w-[46px] h-[46px] rounded-full bg-cream/10 flex items-center justify-center">
          <span className="text-[10px] tracking-[0.18em]">日知</span>
        </div>
      </div>
      <div className="min-w-0">
        <p className="text-[10px] text-cream/50 tracking-[0.18em]">{hint}</p>
        <p className="font-display text-[17px] leading-snug mt-0.5">{line || '等出门卡生成'}</p>
      </div>
    </div>
  )
}

const INSIGHT_STYLE = {
  idle: 'bg-sand text-ink',
  missing: 'bg-accent/10 text-accent',
  ready: 'bg-sage/15 text-[#3f5340]',
  notice: 'bg-cream text-soft border border-sand',
}

export function InsightList({ items }) {
  if (!items?.length) return null
  return (
    <ul className="flex flex-col gap-1.5">
      {items.map((item, i) => (
        <li
          key={`${item.text}-${i}`}
          className={`text-[13px] leading-snug px-3 py-2 rounded-xl ${INSIGHT_STYLE[item.kind] || INSIGHT_STYLE.notice}`}
        >
          {item.text}
        </li>
      ))}
    </ul>
  )
}

export function AIBadge({ powered }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
        powered ? 'bg-accent/10 text-accent' : 'bg-sand text-soft'
      }`}
    >
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-2.5 h-2.5">
        <path d="M12 2l2.1 6.5L21 10l-6.9 1.5L12 18l-2.1-6.5L3 10l6.9-1.5z" />
      </svg>
      {powered ? 'Qwen AI' : '本地引擎'}
    </span>
  )
}
