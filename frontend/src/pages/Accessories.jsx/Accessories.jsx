import { useState, useEffect, useRef } from 'react'

const CATEGORIES = ['全部', '项链', '耳环', '手链', '戒指', '手表', '包包', '腰带', '帽子', '其他']
const STYLES = ['百搭', '休闲', '街头', '轻熟', '优雅', '正式', '运动']
const MATERIALS = ['金属', '皮质', '珍珠', '宝石', '木质', '编织', '帆布', '塑料', '其他']

const API_BASE = 'http://localhost:8000'

export default function Accessories() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState(null)
  const [file, setFile] = useState(null)
  const [form, setForm] = useState({ name: '', category: '项链', style: '百搭', material: '金属', color: '', visual_weight: 1 })
  const [filterCategory, setFilterCategory] = useState('全部')
  const fileRef = useRef(null)

  useEffect(() => { loadItems() }, [filterCategory])

  const loadItems = async () => {
    try {
      const res = await fetch(`${API_BASE}/accessories/list?category=${filterCategory}`)
      const data = await res.json()
      setItems(data.items || [])
    } catch (e) { console.error('加载失败', e) }
  }

  const handleFile = (e) => {
    const f = e.target.files[0]
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }

  const submit = async () => {
    if (!file) return alert('请先选择图片')
    if (!form.name) return alert('请填写名称')
    setLoading(true)
    try {
      const data = new FormData()
      data.append('file', file)
      data.append('name', form.name)
      data.append('category', form.category)
      data.append('style', form.style)
      data.append('material', form.material)
      data.append('color', form.color)
      data.append('visual_weight', form.visual_weight)

      const res = await fetch(`${API_BASE}/accessories/upload`, { method: 'POST', body: data })
      if (!res.ok) throw new Error('上传失败')
      alert('上传成功！')
      setPreview(null)
      setFile(null)
      setForm({ ...form, name: '', color: '' })
      loadItems()
    } catch (e) { alert('上传失败：' + e.message) }
    finally { setLoading(false) }
  }

  const deleteItem = async (id) => {
    if (!confirm('确定删除吗？')) return
    try {
      await fetch(`${API_BASE}/accessories/${id}`, { method: 'DELETE' })
      loadItems()
    } catch (e) { alert('删除失败') }
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      <div className="bg-black text-white p-4 sticky top-0 z-10">
        <h1 className="text-lg font-bold">我的配饰</h1>
        <p className="text-xs text-gray-400 mt-1">拍照上传，AI帮你智能搭配</p>
      </div>

      <div className="p-4 space-y-4">
        <div className="bg-white rounded-2xl p-4 shadow-sm space-y-3">
          <h2 className="font-semibold text-sm">添加新配饰</h2>
          
          <div onClick={() => fileRef.current?.click()} className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-gray-500 transition-colors">
            {preview ? <img src={preview} className="w-full h-40 object-contain rounded-lg" /> : <div className="text-gray-400"><div className="text-3xl mb-2">📷</div><div className="text-sm">点击拍照或选择图片</div></div>}
          </div>
          <input ref={fileRef} type="file" accept="image/*" capture="environment" className="hidden" onChange={handleFile} />

          <input placeholder="物品名称，如：珍珠项链" value={form.name} onChange={e => setForm({...form, name: e.target.value})} className="w-full p-3 border rounded-lg text-sm" />

          <div className="grid grid-cols-2 gap-2">
            <select value={form.category} onChange={e => setForm({...form, category: e.target.value})} className="p-3 border rounded-lg text-sm bg-white">
              {CATEGORIES.filter(c => c !== '全部').map(c => <option key={c}>{c}</option>)}
            </select>
            <select value={form.style} onChange={e => setForm({...form, style: e.target.value})} className="p-3 border rounded-lg text-sm bg-white">
              {STYLES.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <select value={form.material} onChange={e => setForm({...form, material: e.target.value})} className="p-3 border rounded-lg text-sm bg-white">
              {MATERIALS.map(m => <option key={m}>{m}</option>)}
            </select>
            <input placeholder="颜色（如：金色、黑色）" value={form.color} onChange={e => setForm({...form, color: e.target.value})} className="p-3 border rounded-lg text-sm" />
          </div>

          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">视觉重量：</span>
            {[1, 2, 3].map(w => (
              <button key={w} onClick={() => setForm({...form, visual_weight: w})} className={`px-3 py-1 rounded-full text-xs transition-colors ${form.visual_weight === w ? 'bg-black text-white' : 'bg-gray-100 text-gray-600'}`}>
                {w === 1 ? '轻' : w === 2 ? '中' : '重'}
              </button>
            ))}
            <span className="text-xs text-gray-400 ml-2">大/夸张=重，小/简约=轻</span>
          </div>

          <button onClick={submit} disabled={loading} className="w-full py-3 bg-black text-white rounded-xl font-medium disabled:opacity-50">
            {loading ? '上传中...' : '保存到配饰库'}
          </button>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-2">
          {CATEGORIES.map(c => (
            <button key={c} onClick={() => setFilterCategory(c)} className={`px-3 py-1 rounded-full text-xs whitespace-nowrap transition-colors ${filterCategory === c ? 'bg-black text-white' : 'bg-white text-gray-600'}`}>
              {c}
            </button>
          ))}
        </div>

        <div className="space-y-3">
          <h2 className="font-semibold text-sm">已添加的配饰（{items.length}）</h2>
          {items.length === 0 && <div className="text-center text-gray-400 py-8 text-sm">还没有配饰，添加几件让AI帮你搭配吧</div>}
          {items.map(item => (
            <div key={item.id} className="bg-white rounded-xl p-3 flex gap-3 shadow-sm">
              <img src={`${API_BASE}${item.image_url}`} className="w-20 h-20 object-cover rounded-lg bg-gray-100" />
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-medium text-sm">{item.name}</div>
                    <div className="text-xs text-gray-500 mt-1">{item.category} · {item.style} · {item.material}</div>
                    <div className="text-xs text-gray-400 mt-0.5">{item.color} · 视觉重量：{item.visual_weight === 1 ? '轻' : item.visual_weight === 2 ? '中' : '重'}</div>
                  </div>
                  <button onClick={() => deleteItem(item.id)} className="text-gray-400 hover:text-red-500 text-xs px-2">删除</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
