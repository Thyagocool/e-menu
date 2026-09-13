import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/services/api'
import type { Product } from '../../shared/services/api'
import { getRestaurantId } from '../../shared/utils/restaurant'

export default function ProductsPage() {
  const restaurantId = getRestaurantId()
  const queryClient = useQueryClient()

  const { data: products } = useQuery({
    queryKey: ['products', restaurantId],
    queryFn: () => api.get<Product[]>(`/restaurants/${restaurantId}/products`),
    enabled: !!restaurantId,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['products'] })

  const toggle = useMutation({
    mutationFn: (p: Product) =>
      api.put<Product>(`/products/${p.id}`, {
        status: p.status === 'active' ? 'inactive' : 'active',
      }),
    onSuccess: invalidate,
  })

  const remove = useMutation({
    mutationFn: (id: number) => api.delete(`/products/${id}`),
    onSuccess: invalidate,
  })

  return (
    <section className="card">
      <div className="page-head">
        <h1>Produtos</h1>
        <Link to="/produtos/novo" className="btn">
          + Novo produto
        </Link>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>Imagem</th>
            <th>Nome</th>
            <th>Preço</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {products?.map((p) => (
            <tr key={p.id}>
              <td>
                {p.image_url && <img className="thumb" src={p.image_url} alt={p.name} />}
              </td>
              <td>
                <Link to={`/produtos/${p.id}`}>{p.name}</Link>
              </td>
              <td>R$ {p.base_price}</td>
              <td>{p.status}</td>
              <td className="table-actions">
                <button className="btn-small" onClick={() => toggle.mutate(p)}>
                  {p.status === 'active' ? 'Desativar' : 'Ativar'}
                </button>
                <button className="btn-small danger" onClick={() => remove.mutate(p.id)}>
                  Excluir
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}