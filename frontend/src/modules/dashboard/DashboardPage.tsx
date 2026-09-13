import { Link } from 'react-router-dom'

export default function DashboardPage() {
  return (
    <section className="card">
      <h1>Painel</h1>
      <p>Administre seu restaurante e catálogo.</p>
      <div className="page-head">
        <Link to="/restaurante" className="card link-card">
          <h3>Restaurante</h3>
          <span>Nome, WhatsApp, endereço, taxa de entrega</span>
        </Link>
        <Link to="/categorias" className="card link-card">
          <h3>Categorias</h3>
          <span>Organize seus produtos</span>
        </Link>
        <Link to="/produtos" className="card link-card">
          <h3>Produtos</h3>
          <span>Itens, preços, variações e adicionais</span>
        </Link>
        <Link to="/adicionais" className="card link-card">
          <h3>Adicionais</h3>
          <span>Extras vinculáveis aos produtos</span>
        </Link>
      </div>
    </section>
  )
}