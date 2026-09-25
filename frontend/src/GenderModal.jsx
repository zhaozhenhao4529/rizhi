import { useState, useEffect } from 'react'

export default function GenderModal({ onSelect }) {
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('rizhi_gender')
    if (!saved) {
      setIsOpen(true)
    }
  }, [])

  const selectGender = (gender) => {
    localStorage.setItem('rizhi_gender', gender)
    setIsOpen(false)
    onSelect?.(gender)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-sm rounded-2xl bg-white shadow-lg p-6">
        <h2 className="text-xl font-bold text-center mb-2">欢迎使用日知</h2>
        <p className="text-sm text-gray-500 text-center mb-6">
          选择您的性别，我们将为您推荐更合适的穿搭
        </p>
        
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => selectGender('female')}
            className="flex flex-col items-center gap-2 p-5 rounded-xl bg-pink-50 border-2 border-transparent hover:border-pink-400 active:scale-95 transition-all"
          >
            <span className="text-4xl">👩</span>
            <span className="font-semibold text-sm">女生</span>
          </button>
          
          <button
            onClick={() => selectGender('male')}
            className="flex flex-col items-center gap-2 p-5 rounded-xl bg-blue-50 border-2 border-transparent hover:border-blue-400 active:scale-95 transition-all"
          >
            <span className="text-4xl">👨</span>
            <span className="font-semibold text-sm">男生</span>
          </button>
        </div>
        
        <p className="text-xs text-gray-400 text-center mt-4">
          可随时在设置中更改
        </p>
      </div>
    </div>
  )
}
