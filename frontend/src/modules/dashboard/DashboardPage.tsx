import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../shared/services/api'
import { getRestaurantId } from '../../shared/utils/restaurant'

function formatMoney(value: string) {
  const n = Number(value)
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export default function DashboardPage() {
  const restaurantId = getRestaurantId()

  const { data: dashboard } = useQuery({
    queryKey: ['dashboard', restaurantId],
    queryFn: () => api.getDashboard(restaurantId!),
    enabled: !!restaurantId,
    refetchInterval: 30_000,
  })

  if (!restaurantId) {
    return (
      <section className="card">
        <h1>Painel</h1>
        <p>
          Configure seu restaurante primeiro para ver as métricas.
        </p>
        <Link to="/restaurante" className="btn">
          Configurar restaurante
        </Link>
      </section>
    )
  }

  return (
    <section className="card">
      <h1>Painel</h1>
      <div className="dashboard-grid">
        <div className="card stat-card">
          <span className="stat-label">Pedidos hoje</span>
          <span className="stat-value">{dashboard?.orders_today ?? 0}</span>
        </div>
        <div className="card stat-card">
          <span className="stat-label">Faturamento hoje</span>
          <span className="stat-value">
            {dashboard ? formatMoney(dashboard.revenue_today) : '-'}
          </span>
        </div>
        <div className="card stat-card">
          <span className="stat-label">Pedidos pendentes</span>
          <span className="stat-value">{dashboard?.pending_orders ?? 0}</span>
        </div>
      </div>
      <div className="page-head">
        <h2>Mais pedidos</h2>
      </div>
      <ul className="top-products">
        {dashboard?.top_products.map((p) => (
          <li key={p.name}>
            <span>
              {p.quantity}x {p.name}
            </span>
            <span className="muted">{formatMoney(p.revenue)}</span>
          </li>
        ))}
        {dashboard?.top_products.length === 0 && <li className="muted">Nenhum produto pedido ainda.</li>}
      </ul>
      <div className="page-head">
        <Link to="/pedidos" className="btn">
          Ver pedidos
        </Link>
      </div>
    </section>
  )
}