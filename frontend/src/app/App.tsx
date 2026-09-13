import { Route, Routes } from 'react-router-dom'
import Layout from './Layout.tsx'
import DashboardPage from '../modules/dashboard/DashboardPage.tsx'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<DashboardPage />} />
      </Route>
    </Routes>
  )
}