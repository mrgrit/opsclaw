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
import Community from './pages/portal/Community'
import Board from './pages/portal/Board'
import PostDetail from './pages/portal/PostDetail'
import PostWrite from './pages/portal/PostWrite'
import Profile from './pages/portal/Profile'
import AdminPanel from './pages/portal/AdminPanel'

export default function App() {
  return (
    <BrowserRouter basename="/app">
      <Routes>
        {/* Education Portal — 기본 페이지 */}
        <Route element={<PortalLayout />}>
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
          <Route path="community" element={<Community />} />
          <Route path="community/:slug" element={<Board />} />
          <Route path="community/:slug/write" element={<PostWrite />} />
          <Route path="community/:slug/:postId" element={<PostDetail />} />
          <Route path="profile" element={<Profile />} />
          <Route path="profile/:username" element={<Profile />} />
          <Route path="admin-panel" element={<AdminPanel />} />
        </Route>

        {/* Admin console */}
        <Route path="admin" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="projects" element={<Projects />} />
          <Route path="playbooks" element={<Playbooks />} />
          <Route path="replay" element={<Replay />} />
          <Route path="pow" element={<PoW />} />
          <Route path="agents" element={<Agents />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
