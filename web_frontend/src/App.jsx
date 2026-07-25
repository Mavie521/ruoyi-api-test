import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import TestCasesPage from './pages/TestCasesPage.jsx'
import RunHistoryPage from './pages/RunHistoryPage.jsx'
import RunDetailPage from './pages/RunDetailPage.jsx'
import ReportPage from './pages/ReportPage.jsx'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/tests" element={<TestCasesPage />} />
        <Route path="/runs" element={<RunHistoryPage />} />
        <Route path="/runs/:id" element={<RunDetailPage />} />
        <Route path="/reports" element={<ReportPage />} />
      </Routes>
    </Layout>
  )
}
