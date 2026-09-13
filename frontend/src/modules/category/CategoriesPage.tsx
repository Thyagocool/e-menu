import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/services/api'
import type { Category } from '../../shared/services/api'
import { getRestaurantId } from '../../shared/utils/restaurant'

export default function CategoriesPage() {
  const restaurantId = getRestaurantId()
  const queryClient = useQueryClient()
  const [newName, setNewName] = useState('')
  const [editing, setEditing] = useState<Record<number, string>>({})
  const [error, setError] = useState('')

  const { data: categories } = useQuery({
    queryKey: ['categories', restaurantId],
    queryFn: () => api.get<Category[]>(`/restaurants/${restaurantId}/categories`),
    enabled: !!restaurantId,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['categories'] })

  const create = useMutation({
    mutationFn: (name: string) =>
      api.post<Category>(`/restaurants/${restaurantId}/categories`, { name }),
    onSuccess: () => {
      setNewName('')
      setError('')
      invalidate()
    },
    onError: (err) => setError((err as Error).message),
  })

  const update = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      api.put<Category>(`/categories/${id}`, { name }),
    onSuccess: () => {
      setEditing({})
      invalidate()
    },
  })

  const remove = useMutation({
    mutationFn: (id: number) => api.delete(`/categories/${id}`),
    onSuccess: invalidate,
    onError: (err) => setError((err as Error).message),
  })

  function submitNew(e: FormEvent) {
    e.preventDefault()
    if (newName.trim()) create.mutate(newName.trim())
  }

  return (
    <section className="card">
      <h1>Categorias</h1>
      <form onSubmit={submitNew} className="inline-form">
        <input
          placeholder="Nova categoria (ex: Pizzas)"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
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
            <th>Ordem</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {categories?.map((c) => (
            <tr key={c.id}>
              <td>
                <input
                  className="table-input"
                  value={editing[c.id] ?? c.name}
                  onChange={(e) => setEditing({ ...editing, [c.id]: e.target.value })}
                />
              </td>
              <td>{c.sort_order}</td>
              <td>{c.status}</td>
              <td className="table-actions">
                <button
                  className="btn-small"
                  onClick={() => update.mutate({ id: c.id, name: editing[c.id] ?? c.name })}
                >
                  Salvar
                </button>
                <button className="btn-small danger" onClick={() => remove.mutate(c.id)}>
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