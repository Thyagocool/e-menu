import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import type { PublicProduct, PublicRestaurant } from '../../shared/services/api'
import { api } from '../../shared/services/api'
import './MenuPage.css'

function formatPrice(value: string): string {
  return `R$ ${Number(value).toFixed(2).replace('.', ',')}`
}

function productPrice(product: PublicProduct): { min: number; from: boolean } {
  const prices = product.variants.map((v) => Number(v.price))
  if (prices.length > 0) return { min: Math.min(...prices), from: true }
  return { min: Number(product.base_price), from: false }
}

function whatsappLink(restaurant: PublicRestaurant, text: string): string {
  const digits = (restaurant.whatsapp_phone ?? '').replace(/\D/g, '')
  const number = digits.length <= 11 ? `55${digits}` : digits
  return `https://wa.me/${number}?text=${encodeURIComponent(text)}`
}

interface SheetState {
  product: PublicProduct
  variantId: number | null
  addons: Set<number>
  quantity: number
  note: string
}

function orderMessage(
  restaurant: PublicRestaurant,
  product: PublicProduct,
  state: SheetState,
): string {
  const variant = product.variants.find((v) => v.id === state.variantId)
  const lines = [
    `Olá! Vi o cardápio de ${restaurant.name} e gostaria de pedir:`,
    `- ${product.name}${variant ? ` (${variant.name})` : ''}`,
  ]
  const addons = product.addons.filter((a) => state.addons.has(a.id))
  if (addons.length > 0) {
    lines.push(`- Adicionais: ${addons.map((a) => `${a.name} (+${formatPrice(a.price)})`).join(', ')}`)
  }
  if (state.note.trim()) lines.push(`- Observação: ${state.note.trim()}`)
  lines.push(`- Quantidade: ${state.quantity}`)
  return lines.join('\n')
}

function ProductSheet({
  restaurant,
  state,
  setState,
  onClose,
}: {
  restaurant: PublicRestaurant
  state: SheetState
  setState: (next: SheetState) => void
  onClose: () => void
}) {
  const { product } = state
  const total =
    (state.variantId
      ? Number(product.variants.find((v) => v.id === state.variantId)?.price ?? 0)
      : Number(product.base_price)) +
    product.addons
      .filter((a) => state.addons.has(a.id))
      .reduce((sum, a) => sum + Number(a.price), 0)

  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <button className="sheet-close" onClick={onClose} aria-label="Fechar">
          ×
        </button>
        {product.image_url && <img className="sheet-image" src={product.image_url} alt={product.name} />}
        <h2 className="sheet-title">{product.name}</h2>
        {product.description && <p className="sheet-description">{product.description}</p>}

        {product.variants.length > 0 && (
          <fieldset className="sheet-group">
            <legend>Variação</legend>
            {product.variants.map((v) => (
              <label key={v.id} className="sheet-row">
                <input
                  type="radio"
                  name="variant"
                  checked={state.variantId === v.id}
                  onChange={() => setState({ ...state, variantId: v.id })}
                />
                <span>{v.name}</span>
                <span className="sheet-price">{formatPrice(v.price)}</span>
              </label>
            ))}
          </fieldset>
        )}

        {product.addons.length > 0 && (
          <fieldset className="sheet-group">
            <legend>Adicionais</legend>
            {product.addons.map((a) => (
              <label key={a.id} className="sheet-row">
                <input
                  type="checkbox"
                  checked={state.addons.has(a.id)}
                  onChange={(e) => {
                    const addons = new Set(state.addons)
                    if (e.target.checked) addons.add(a.id)
                    else addons.delete(a.id)
                    setState({ ...state, addons })
                  }}
                />
                <span>{a.name}</span>
                <span className="sheet-price">{a.price === '0' ? 'Grátis' : `+${formatPrice(a.price)}`}</span>
              </label>
            ))}
          </fieldset>
        )}

        <div className="sheet-row sheet-row-note">
          <label htmlFor="note">Observação</label>
          <input
            id="note"
            type="text"
            maxLength={200}
            placeholder="Ex.: sem cebola"
            value={state.note}
            onChange={(e) => setState({ ...state, note: e.target.value })}
          />
        </div>

        <div className="sheet-row sheet-row-qty">
          <label htmlFor="qty">Quantidade</label>
          <select
            id="qty"
            value={state.quantity}
            onChange={(e) => setState({ ...state, quantity: Number(e.target.value) })}
          >
            {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </div>

        <a
          className="sheet-whatsapp"
          href={whatsappLink(restaurant, orderMessage(restaurant, product, state))}
          target="_blank"
          rel="noreferrer"
        >
          Pedir pelo WhatsApp · {formatPrice(String(total))}
        </a>
      </div>
    </div>
  )
}

function ProductCard({
  product,
  onClick,
}: {
  product: PublicProduct
  onClick: () => void
}) {
  const { min, from } = productPrice(product)
  return (
    <button className="product-card" onClick={onClick}>
      {product.image_url ? (
        <img className="product-image" src={product.image_url} alt={product.name} loading="lazy" />
      ) : (
        <div className="product-image product-image-placeholder" />
      )}
      <div className="product-info">
        <h3 className="product-name">{product.name}</h3>
        {product.description && <p className="product-description">{product.description}</p>}
        <span className="product-price">
          {from ? 'a partir de ' : ''}
          {formatPrice(String(min))}
        </span>
      </div>
    </button>
  )
}

export default function MenuPage() {
  const { slug } = useParams<{ slug: string }>()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['public-menu', slug],
    queryFn: () => api.getPublicMenu(slug ?? ''),
    enabled: Boolean(slug),
    retry: false,
  })
  const [sheet, setSheet] = useState<SheetState | null>(null)

  const sections = useMemo(() => {
    if (!data) return []
    const withProducts = data.categories.filter((c) => c.products.length > 0)
    const uncategorized = data.uncategorized_products
    const all = [
      ...withProducts.map((c) => ({ id: c.id, name: c.name, products: c.products })),
      ...(uncategorized.length > 0 ? [{ id: -1, name: 'Outros', products: uncategorized }] : []),
    ]
    return all
  }, [data])

  if (isLoading) return <div className="menu-page">Carregando cardápio…</div>
  if (isError || !data) {
    return (
      <div className="menu-page menu-empty">
        <h1>Cardápio não encontrado</h1>
        <p>Verifique o link ou tente novamente mais tarde.</p>
      </div>
    )
  }

  const { restaurant } = data

  return (
    <div className="menu-page">
      <header className="menu-header">
        <p className="menu-brand">e-menu</p>
        <h1 className="menu-name">{restaurant.name}</h1>
        {restaurant.opening_hours && <p className="menu-meta">{restaurant.opening_hours}</p>}
        {restaurant.address && <p className="menu-meta">{restaurant.address}</p>}
        {Number(restaurant.delivery_fee) > 0 && (
          <p className="menu-meta">Taxa de entrega: {formatPrice(restaurant.delivery_fee)}</p>
        )}
      </header>

      <nav className="menu-nav">
        {sections.map((s) => (
          <a key={s.id} href={`#cat-${s.id}`} className="menu-chip">
            {s.name}
          </a>
        ))}
      </nav>

      <main className="menu-body">
        {sections.map((section) => (
          <section key={section.id} id={`cat-${section.id}`} className="menu-section">
            <h2 className="menu-section-title">{section.name}</h2>
            <div className="menu-products">
              {section.products.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onClick={() =>
                    setSheet({
                      product,
                      variantId: product.variants.length > 0 ? product.variants[0].id : null,
                      addons: new Set(),
                      quantity: 1,
                      note: '',
                    })
                  }
                />
              ))}
            </div>
          </section>
        ))}
      </main>

      {sheet && (
        <ProductSheet
          restaurant={restaurant}
          state={sheet}
          setState={setSheet}
          onClose={() => setSheet(null)}
        />
      )}
    </div>
  )
}