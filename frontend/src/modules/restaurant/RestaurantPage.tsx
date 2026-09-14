import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/services/api'
import type { Restaurant } from '../../shared/services/api'
import { getRestaurantId, setRestaurantId } from '../../shared/utils/restaurant'

interface FormState {
  id: number
  name: string
  slug: string
  phone: string
  whatsapp_phone: string
  address: string
  opening_hours: string
  delivery_fee: string
  status: 'active' | 'inactive'
}

const empty: FormState = {
  id: 0,
  name: '',
  slug: '',
  phone: '',
  whatsapp_phone: '',
  address: '',
  opening_hours: '',
  delivery_fee: '0',
  status: 'active',
}

export default function RestaurantPage() {
  const [form, setForm] = useState<FormState>({ ...empty })
  const [saved, setSaved] = useState(false)
  const queryClient = useQueryClient()
  const restaurantId = getRestaurantId()

  const { data: restaurant } = useQuery({
    queryKey: ['restaurant', restaurantId],
    queryFn: () => api.get<Restaurant>(`/restaurants/${restaurantId}`),
    enabled: !!restaurantId,
  })

  useEffect(() => {
    if (restaurant) {
      setForm({
        id: restaurant.id,
        name: restaurant.name,
        slug: restaurant.slug,
        phone: restaurant.phone ?? '',
        whatsapp_phone: restaurant.whatsapp_phone ?? '',
        address: restaurant.address ?? '',
        opening_hours: restaurant.opening_hours ?? '',
        delivery_fee: restaurant.delivery_fee,
        status: restaurant.status,
      })
    }
  }, [restaurant])

  const save = useMutation({
    mutationFn: async (payload: typeof empty) => {
      if (form.id) {
        const { slug, ...rest } = payload
        return api.put<Restaurant>(`/restaurants/${form.id}`, slug ? { ...rest, slug } : rest)
      }
      return api.post<Restaurant>('/restaurants', payload)
    },
    onSuccess: (result) => {
      setSaved(true)
      setRestaurantId(result.id)
      setForm((f) => ({ ...f, id: result.id }))
      queryClient.invalidateQueries({ queryKey: ['restaurant'] })
      setTimeout(() => setSaved(false), 2000)
    },
  })

  function submit(e: FormEvent) {
    e.preventDefault()
    save.mutate({ ...form, delivery_fee: form.delivery_fee || '0' })
  }

  const field = (name: keyof typeof empty) => ({
    value: form[name],
    onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm({ ...form, [name]: e.target.value }),
  })

  return (
    <section className="card">
      <h1>Restaurante</h1>
      {form.id === 0 && restaurantId && !restaurant ? (
        <p>Restaurante não encontrado. Crie um novo abaixo.</p>
      ) : null}
      <form onSubmit={submit} className="form-grid">
        <label>
          Nome *
          <input required {...field('name')} />
        </label>
        <label>
          Slug (opcional)
          <input placeholder="ex: pizzaria-do-ze" {...field('slug')} />
        </label>
        <label>
          Telefone
          <input {...field('phone')} />
        </label>
        <label>
          WhatsApp
          <input placeholder="+5511999999999" {...field('whatsapp_phone')} />
        </label>
        <label>
          Endereço
          <input {...field('address')} />
        </label>
        <label>
          Horário de atendimento
          <input placeholder="18h às 23h" {...field('opening_hours')} />
        </label>
        <label>
          Taxa de entrega (R$)
          <input type="number" step="0.01" min="0" {...field('delivery_fee')} />
        </label>
        <label>
          Status
          <select
            value={form.status}
            onChange={(e) => setForm({ ...form, status: e.target.value as 'active' | 'inactive' })}
          >
            <option value="active">Ativo</option>
            <option value="inactive">Inativo</option>
          </select>
        </label>
        <div className="form-actions">
          <button type="submit" className="btn">
            Salvar
          </button>
          {saved && <span className="muted">Salvo!</span>}
          {save.isError && <span className="error">Erro: {(save.error as Error).message}</span>}
        </div>
      </form>
      {restaurant?.slug && (
        <div className="qr-box">
          <h3>Cardápio público</h3>
          <p className="muted">
            Link: <a href={`/cardapio/${restaurant.slug}`}>{`/cardapio/${restaurant.slug}`}</a>
          </p>
          <img
            src={api.getQrUrl(restaurant.id)}
            alt="QR Code do cardápio"
            width={180}
            height={180}
          />
        </div>
      )}
    </section>
  )
}