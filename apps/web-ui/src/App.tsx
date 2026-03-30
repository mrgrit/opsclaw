import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import Playbooks from './pages/Playbooks'
import Replay from './pages/Replay'
import PoW from './pages/PoW'
import Settings from './pages/Settings'
import Agents from './pages/Agents'

// Portal pages
import PortalLayout from './components/portal/PortalLayout'
import PortalHome from './pages/portal/Home'
import PortalLogin from './pages/portal/Login'
import PortalEducation from './pages/portal/Education'
import PortalLecture from './pages/portal/Lecture'
import PortalNovel from './pages/portal/Novel'
import PortalChapter from './pages/portal/Chapter'
import PortalCTF from './pages/portal/CTF'
import PortalTerminal from './pages/portal/Terminal'
import PortalPapers from './pages/portal/Papers'

export default function App() {
  return (
    <BrowserRouter basename="/app">
      <Routes>
        {/* Admin console */}
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="projects" element={<Projects />} />
          <Route path="playbooks" element={<Playbooks />} />
          <Route path="replay" element={<Replay />} />
          <Route path="pow" element={<PoW />} />
          <Route path="agents" element={<Agents />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        {/* Education Portal */}
        <Route path="portal" element={<PortalLayout />}>
          <Route index element={<PortalHome />} />
          <Route path="login" element={<PortalLogin />} />
          <Route path="education" element={<PortalEducation />} />
          <Route path="education/:course" element={<PortalEducation />} />
          <Route path="education/:course/:week" element={<PortalLecture />} />
          <Route path="novel" element={<PortalNovel />} />
          <Route path="novel/:vol" element={<PortalNovel />} />
          <Route path="novel/:vol/:chapter" element={<PortalChapter />} />
          <Route path="ctf" element={<PortalCTF />} />
          <Route path="terminal" element={<PortalTerminal />} />
          <Route path="papers" element={<PortalPapers />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
