import { Link, Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <div>
      <header className="header">
        <div className="container header-inner">
          <Link to="/" className="brand">
            e-menu
          </Link>
          <nav className="nav">
            <Link to="/">Dashboard</Link>
            <Link to="/restaurante">Restaurante</Link>
            <Link to="/categorias">Categorias</Link>
            <Link to="/produtos">Produtos</Link>
            <Link to="/adicionais">Adicionais</Link>
          </nav>
        </div>
      </header>
      <main className="container">
        <Outlet />
      </main>
      <footer className="footer">
        <div className="container">e-menu — cardápio &amp; garçom IA</div>
      </footer>
    </div>
  )
}