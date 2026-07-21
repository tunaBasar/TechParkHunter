import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Building2, Radar } from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/companies', label: 'Şirketler', icon: Building2 },
  { to: '/scraping', label: 'Scraping', icon: Radar },
];

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="logo gradient-text">🏗️ TechPark Hunter</span>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `sidebar-link${isActive ? ' active' : ''}`
            }
          >
            <Icon />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">v1.0.0</div>
    </aside>
  );
}

export default Sidebar;
