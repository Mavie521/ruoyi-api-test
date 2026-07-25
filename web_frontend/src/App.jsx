import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import TestCasesPage from './pages/TestCasesPage.jsx'
import RunHistoryPage from './pages/RunHistoryPage.jsx'
import RunDetailPage from './pages/RunDetailPage.jsx'
import ReportPage from './pages/ReportPage.jsx'
import EnvironmentPage from './pages/EnvironmentPage.jsx'
import NotifySettingsPage from './pages/NotifySettingsPage.jsx'
import MockPage from './pages/MockPage.jsx'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/tests" element={<TestCasesPage />} />
        <Route path="/runs" element={<RunHistoryPage />} />
        <Route path="/runs/:id" element={<RunDetailPage />} />
        <Route path="/reports" element={<ReportPage />} />
        <Route path="/environments" element={<EnvironmentPage />} />
        <Route path="/settings/notify" element={<NotifySettingsPage />} />
        <Route path="/mock" element={<MockPage />} />
      </Routes>
    </Layout>
  )
}
