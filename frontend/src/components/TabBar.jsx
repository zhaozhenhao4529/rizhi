import { NavLink, useNavigate } from 'react-router-dom'

const tabs = [
  { path: '/', label: '今日', icon: IconToday },
  { path: '/snap', label: '一拍', icon: IconSnap },
  { path: '/upload', label: '', icon: null },
  { path: '/day', label: '一日', icon: IconDay },
  { path: '/wardrobe', label: '衣橱', icon: IconWardrobe },
]

function IconToday({ active }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={active ? 2.2 : 1.6} className="w-6 h-6">
      <circle cx="12" cy="12" r="8" />
      <path d="M12 8v4l2.5 2" strokeLinecap="round" />
    </svg>
  )
}
function IconSnap({ active }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={active ? 2.2 : 1.6} className="w-6 h-6">
      <path d="M4 8h3l1.5-2h7L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z" strokeLinejoin="round" />
      <circle cx="12" cy="13" r="3" />
    </svg>
  )
}
function IconDay({ active }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={active ? 2.2 : 1.6} className="w-6 h-6">
      <path d="M6 4h9a3 3 0 0 1 3 3v13H8a2 2 0 0 0-2 2V4z" strokeLinejoin="round" />
      <path d="M9 8h6M9 12h6" strokeLinecap="round" />
    </svg>
  )
}
function IconWardrobe({ active }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={active ? 2.2 : 1.6} className="w-6 h-6">
      <rect x="4" y="3" width="16" height="18" rx="1.5" />
      <path d="M12 3v18M9 8v3M15 8v3" strokeLinecap="round" />
    </svg>
  )
}

export default function TabBar() {
  const navigate = useNavigate()
  return (
    <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[430px] bg-card/95 backdrop-blur border-t border-sand z-50">
      <div className="grid grid-cols-5 h-16 items-end">
        {tabs.map((tab) =>
          tab.icon === null ? (
            <div key="fab" className="flex justify-center">
              <button
                onClick={() => navigate('/upload')}
                className="relative -top-5 w-14 h-14 rounded-full bg-accent text-white shadow-lift flex items-center justify-center active:scale-95 transition-transform"
                aria-label="录入衣物"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.4} className="w-7 h-7">
                  <path d="M12 5v14M5 12h14" strokeLinecap="round" />
                </svg>
              </button>
            </div>
          ) : (
            <NavLink
              key={tab.path}
              to={tab.path}
              end={tab.path === '/'}
              className={({ isActive }) =>
                `flex flex-col items-center gap-0.5 pb-2 pt-2 transition-colors ${
                  isActive ? 'text-accent' : 'text-soft'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <tab.icon active={isActive} />
                  <span className={`text-[11px] ${isActive ? 'font-semibold' : ''}`}>{tab.label}</span>
                </>
              )}
            </NavLink>
          )
        )}
      </div>
    </nav>
  )
}
