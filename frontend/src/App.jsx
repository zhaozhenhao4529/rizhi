import { Routes, Route } from 'react-router-dom'
import TabBar from './components/TabBar'
import Home from './pages/Home'
import Wardrobe from './pages/Wardrobe'
import Upload from './pages/Upload'
import Calendar from './pages/Calendar'
import Diagnosis from './pages/Diagnosis'
import Snap from './pages/Snap'
import Day from './pages/Day'
import About from './pages/About'

export default function App() {
  return (
    <div className="app-shell">
      <div className="pb-24">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/snap" element={<Snap />} />
          <Route path="/day" element={<Day />} />
          <Route path="/about" element={<About />} />
          <Route path="/wardrobe" element={<Wardrobe />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/calendar" element={<Calendar />} />
          <Route path="/diagnosis" element={<Diagnosis />} />
        </Routes>
      </div>
      <TabBar />
    </div>
  )
}
