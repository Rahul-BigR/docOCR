import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  ScanText, LayoutGrid, BarChart3, MessageSquare,
  LogOut, Menu, X, Hexagon, ChevronRight, Home
} from 'lucide-react';
import styles from './Layout.module.css';

const NAV = [
  { to: '/app/analyzer',  label: 'Analyzer',    icon: ScanText },
  { to: '/app/records',   label: 'All Records',  icon: LayoutGrid },
  { to: '/app/analytics', label: 'Analytics',    icon: BarChart3 },
  { to: '/app/chatbot',   label: 'Chatbot',      icon: MessageSquare },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className={styles.shell}>
      {/* Mobile overlay */}
      {open && <div className={styles.overlay} onClick={() => setOpen(false)} />}

      {/* Sidebar */}
      <aside className={`${styles.sidebar} ${open ? styles.sidebarOpen : ''}`}>
        <div className={styles.brand}>
          <Link to="/" className={styles.brandLink}>
            <Hexagon size={24} strokeWidth={1.5} className={styles.brandIcon} />
            <div>
              <div className={styles.brandName}>DocOCR</div>
              <div className={styles.brandTag}>Financial Intelligence</div>
            </div>
          </Link>
        </div>

        <nav className={styles.nav}>
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`
              }
            >
              <Icon size={18} strokeWidth={2} />
              <span>{label}</span>
              <ChevronRight size={14} className={styles.navArrow} />
            </NavLink>
          ))}
        </nav>

        <div className={styles.sidebarFooter}>
          <div className={styles.userInfo}>
            <div className={styles.userAvatar}>
              {user?.username?.[0]?.toUpperCase() || 'U'}
            </div>
            <div>
              <div className={styles.userName}>{user?.username}</div>
              <div className={styles.userRole}>Analyst</div>
            </div>
          </div>
          <button className={styles.logoutBtn} onClick={handleLogout}>
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className={styles.main}>
        <header className={styles.topbar}>
          <button className={styles.menuBtn} onClick={() => setOpen(!open)}>
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className={styles.topbarBrand}>
            <Hexagon size={18} strokeWidth={1.5} style={{ color: 'var(--indigo)' }} />
            <span>DocOCR</span>
          </div>
          <div className={styles.topbarUser}>
            <div className={styles.userAvatarSm}>
              {user?.username?.[0]?.toUpperCase() || 'U'}
            </div>
          </div>
        </header>

        <main className={styles.content}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
