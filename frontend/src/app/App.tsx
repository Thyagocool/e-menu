import { Route, Routes } from 'react-router-dom'
import Layout from './Layout.tsx'
import DashboardPage from '../modules/dashboard/DashboardPage.tsx'
import RestaurantPage from '../modules/restaurant/RestaurantPage.tsx'
import CategoriesPage from '../modules/category/CategoriesPage.tsx'
import ProductsPage from '../modules/product/ProductsPage.tsx'
import ProductFormPage from '../modules/product/ProductFormPage.tsx'
import AddonsPage from '../modules/product/AddonsPage.tsx'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/restaurante" element={<RestaurantPage />} />
        <Route path="/categorias" element={<CategoriesPage />} />
        <Route path="/produtos" element={<ProductsPage />} />
        <Route path="/produtos/novo" element={<ProductFormPage />} />
        <Route path="/produtos/:id" element={<ProductFormPage />} />
        <Route path="/adicionais" element={<AddonsPage />} />
      </Route>
    </Routes>
  )
}