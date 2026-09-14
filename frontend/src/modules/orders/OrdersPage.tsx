import { Fragment, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ORDER_STATUSES } from '../../shared/services/api'
import type { OrderStatus } from '../../shared/services/api'
import { getRestaurantId } from '../../shared/utils/restaurant'

function formatMoney(value: string) {
  const n = Number(value)
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export default function OrdersPage() {
  const restaurantId = getRestaurantId()
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState('')
  const [statusEdit, setStatusEdit] = useState<Record<number, OrderStatus>>({})
  const [expanded, setExpanded] = useState<number | null>(null)

  const { data: orders } = useQuery({
    queryKey: ['orders', restaurantId, filter],
    queryFn: () => api.listOrders(restaurantId!, filter || undefined),
    enabled: !!restaurantId,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['orders'] })

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: OrderStatus }) =>
      api.updateOrderStatus(id, status),
    onSuccess: invalidate,
  })

  return (
    <section className="card">
      <h1>Pedidos</h1>
      <div className="inline-form">
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">Todos os status</option>
          {ORDER_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      {orders?.length === 0 && <p>Nenhum pedido ainda.</p>}
      <table className="table">
        <thead>
          <tr>
            <th>#</th>
            <th>Cliente</th>
            <th>Horário</th>
            <th>Tipo</th>
            <th>Pagamento</th>
            <th>Total</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {orders?.map((order) => (
            <Fragment key={order.id}>
              <tr>
                <td>{order.id}</td>
                <td>{order.customer_name ?? '-'}</td>
                <td>
                  {order.created_at
                    ? new Date(order.created_at).toLocaleString('pt-BR')
                    : '-'}
                </td>
                <td>{order.delivery_type}</td>
                <td>{order.payment_method}</td>
                <td>{formatMoney(order.total)}</td>
                <td>
                  <select
                    value={statusEdit[order.id] ?? order.status}
                    onChange={(e) =>
                      setStatusEdit({ ...statusEdit, [order.id]: e.target.value as OrderStatus })
                    }
                  >
                    {ORDER_STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="table-actions">
                  <button
                    className="btn-small"
                    onClick={() =>
                      updateStatus.mutate({
                        id: order.id,
                        status: statusEdit[order.id] ?? order.status,
                      })
                    }
                  >
                    Salvar
                  </button>
                  <button className="btn-small" onClick={() => setExpanded(expanded === order.id ? null : order.id)}>
                    {expanded === order.id ? 'Fechar' : 'Itens'}
                  </button>
                </td>
              </tr>
              {expanded === order.id && (
                <tr className="order-detail">
                  <td colSpan={8}>
                    <ul>
                      {order.items.map((item, i) => (
                        <li key={i}>
                          {item.quantity}x {item.product_name}
                          {item.variant_name ? ` (${item.variant_name})` : ''} —{' '}
                          {formatMoney(item.line_total)}
                          {item.addons.length > 0 && (
                            <ul>
                              {item.addons.map((a, j) => (
                                <li key={j}>
                                  + {a.name} ({formatMoney(a.price)})
                                </li>
                              ))}
                            </ul>
                          )}
                        </li>
                      ))}
                    </ul>
                    <p>
                      Subtotal: {formatMoney(order.subtotal)} · Taxa:{' '}
                      {formatMoney(order.delivery_fee)}
                      {order.address ? ` · Entrega: ${order.address}` : ''}
                    </p>
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </section>
  )
}