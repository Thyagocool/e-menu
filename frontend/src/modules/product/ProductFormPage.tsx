import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  api,
} from '../../shared/services/api'
import type {
  Addon,
  Category,
  ProductDetail,
  Variant,
} from '../../shared/services/api'
import { getRestaurantId } from '../../shared/utils/restaurant'

interface VariantDraft {
  id?: number
  name: string
  price: string
}

interface ProductForm {
  name: string
  category_id: string
  description: string
  base_price: string
  status: 'active' | 'inactive'
  image_url: string
}

export default function ProductFormPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const restaurantId = getRestaurantId()
  const queryClient = useQueryClient()
  const isEdit = !!id

  const [form, setForm] = useState<ProductForm>({
    name: '',
    category_id: '',
    description: '',
    base_price: '',
    status: 'active',
    image_url: '',
  })
  const [variants, setVariants] = useState<VariantDraft[]>([])
  const [selectedAddons, setSelectedAddons] = useState<number[]>([])
  const [error, setError] = useState('')

  const { data: categories } = useQuery({
    queryKey: ['categories', restaurantId],
    queryFn: () => api.get<Category[]>(`/restaurants/${restaurantId}/categories`),
    enabled: !!restaurantId,
  })

  const { data: addons } = useQuery({
    queryKey: ['addons', restaurantId],
    queryFn: () => api.get<Addon[]>(`/restaurants/${restaurantId}/addons`),
    enabled: !!restaurantId,
  })

  const { data: product } = useQuery({
    queryKey: ['product', id],
    queryFn: () => api.get<ProductDetail>(`/products/${id}`),
    enabled: isEdit,
  })

  useEffect(() => {
    if (product) {
      setForm({
        name: product.name,
        category_id: product.category_id ? String(product.category_id) : '',
        description: product.description ?? '',
        base_price: product.base_price,
        status: product.status,
        image_url: product.image_url ?? '',
      })
      setVariants(product.variants.map((v: Variant) => ({ id: v.id, name: v.name, price: v.price })))
      setSelectedAddons(product.addons.map((a) => a.id))
    }
  }, [product])

  const upload = useMutation({
    mutationFn: (file: File) => api.upload(file),
    onSuccess: (result) => setForm((f) => ({ ...f, image_url: result.url })),
  })

  const save = useMutation({
    mutationFn: async () => {
      const base = {
        name: form.name,
        category_id: form.category_id ? Number(form.category_id) : null,
        description: form.description || null,
        base_price: form.base_price,
        status: form.status,
        image_url: form.image_url || null,
      }
      let productId: number
      if (isEdit) {
        const updated = await api.put<ProductDetail>(`/products/${id}`, base)
        productId = updated.id
      } else {
        const created = await api.post<ProductDetail>(`/restaurants/${restaurantId}/products`, base)
        productId = created.id
      }

      for (const v of variants) {
        if (!v.name || !v.price) continue
        if (v.id) {
          await api.put(`/variants/${v.id}`, { name: v.name, price: v.price })
        } else {
          await api.post(`/products/${productId}/variants`, { name: v.name, price: v.price })
        }
      }

      const current = await api.get<ProductDetail>(`/products/${productId}`)
      const currentAddonIds = current.addons.map((a) => a.id)
      for (const addonId of currentAddonIds) {
        if (!selectedAddons.includes(addonId)) {
          await api.delete(`/products/${productId}/addons/${addonId}`)
        }
      }
      for (const addonId of selectedAddons) {
        if (!currentAddonIds.includes(addonId)) {
          await api.post(`/products/${productId}/addons`, { addon_id: addonId })
        }
      }
      return productId
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      navigate('/produtos')
    },
    onError: (err) => setError((err as Error).message),
  })

  function submit(e: FormEvent) {
    e.preventDefault()
    save.mutate()
  }

  function addVariant() {
    setVariants([...variants, { name: '', price: '' }])
  }

  return (
    <section className="card">
      <h1>{isEdit ? 'Editar produto' : 'Novo produto'}</h1>
      <form onSubmit={submit} className="form-grid">
        <label>
          Nome *
          <input
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </label>
        <label>
          Categoria
          <select
            value={form.category_id}
            onChange={(e) => setForm({ ...form, category_id: e.target.value })}
          >
            <option value="">Sem categoria</option>
            {categories?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Preço base (R$) *
          <input
            required
            type="number"
            step="0.01"
            min="0"
            value={form.base_price}
            onChange={(e) => setForm({ ...form, base_price: e.target.value })}
          />
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
        <label className="full">
          Descrição
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </label>

        <div className="full">
          <h3>Imagem</h3>
          {form.image_url && <img className="thumb big" src={form.image_url} alt="produto" />}
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => e.target.files?.[0] && upload.mutate(e.target.files[0])}
          />
          {upload.isError && <p className="error">Erro no upload: {(upload.error as Error).message}</p>}
        </div>

        <div className="full">
          <h3>
            Variações/tamanhos{' '}
            <button type="button" className="btn-small" onClick={addVariant}>
              + adicionar
            </button>
          </h3>
          {variants.map((v, i) => (
            <div key={i} className="inline-form">
              <input
                placeholder="Nome (ex: Grande)"
                value={v.name}
                onChange={(e) =>
                  setVariants(variants.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)))
                }
              />
              <input
                type="number"
                step="0.01"
                min="0"
                placeholder="Preço"
                value={v.price}
                onChange={(e) =>
                  setVariants(variants.map((x, j) => (j === i ? { ...x, price: e.target.value } : x)))
                }
              />
              <button
                type="button"
                className="btn-small danger"
                onClick={() => setVariants(variants.filter((_, j) => j !== i))}
              >
                Remover
              </button>
            </div>
          ))}
        </div>

        <div className="full">
          <h3>Adicionais</h3>
          <div className="checkbox-list">
            {addons?.map((a) => (
              <label key={a.id}>
                <input
                  type="checkbox"
                  checked={selectedAddons.includes(a.id)}
                  onChange={(e) =>
                    setSelectedAddons(
                      e.target.checked
                        ? [...selectedAddons, a.id]
                        : selectedAddons.filter((x) => x !== a.id)
                    )
                  }
                />
                {a.name} (+R$ {a.price})
              </label>
            ))}
            {addons?.length === 0 && (
              <p className="muted">Nenhum adicional cadastrado ainda.</p>
            )}
          </div>
        </div>

        {error && <p className="error full">{error}</p>}
        <div className="form-actions full">
          <button type="submit" className="btn" disabled={save.isPending}>
            {save.isPending ? 'Salvando...' : 'Salvar'}
          </button>
          <button type="button" onClick={() => navigate('/produtos')} className="btn-secondary">
            Cancelar
          </button>
        </div>
      </form>
    </section>
  )
}