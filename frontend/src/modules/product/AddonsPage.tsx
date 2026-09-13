import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/services/api'
import type { Addon } from '../../shared/services/api'
import { getRestaurantId } from '../../shared/utils/restaurant'

export default function AddonsPage() {
  const restaurantId = getRestaurantId()
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [price, setPrice] = useState('')
  const [error, setError] = useState('')

  const { data: addons } = useQuery({
    queryKey: ['addons', restaurantId],
    queryFn: () => api.get<Addon[]>(`/restaurants/${restaurantId}/addons`),
    enabled: !!restaurantId,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['addons'] })

  const create = useMutation({
    mutationFn: () =>
      api.post<Addon>(`/restaurants/${restaurantId}/addons`, { name, price: price || '0' }),
    onSuccess: () => {
      setName('')
      setPrice('')
      setError('')
      invalidate()
    },
    onError: (err) => setError((err as Error).message),
  })

  const remove = useMutation({
    mutationFn: (id: number) => api.delete(`/addons/${id}`),
    onSuccess: invalidate,
  })

  function submit(e: FormEvent) {
    e.preventDefault()
    if (name.trim()) create.mutate()
  }

  return (
    <section className="card">
      <h1>Adicionais</h1>
      <p className="muted">
        Adicionais são itens extras vinculáveis a produtos (ex: borda de catupiry, bacon).
      </p>
      <form onSubmit={submit} className="inline-form">
        <input placeholder="Nome (ex: Borda Catupiry)" value={name} onChange={(e) => setName(e.target.value)} />
        <input
          type="number"
          step="0.01"
          min="0"
          placeholder="Preço"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
        />
        <button className="btn" type="submit">
          Adicionar
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      <table className="table">
        <thead>
          <tr>
            <th>Nome</th>
            <th>Preço</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {addons?.map((a) => (
            <tr key={a.id}>
              <td>{a.name}</td>
              <td>R$ {a.price}</td>
              <td>{a.status}</td>
              <td className="table-actions">
                <button className="btn-small danger" onClick={() => remove.mutate(a.id)}>
                  Desativar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}