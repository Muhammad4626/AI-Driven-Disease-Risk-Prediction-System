import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Brain, Map, FileText, Settings, Shield } from 'lucide-react';
import styles from './Sidebar.module.css';

interface SidebarProps {
  isDarkMode?: boolean;
}

export function Sidebar({ isDarkMode = false }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();
  
  const menuItems = [
    { id: 'dashboard', path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'predictions', path: '/predictions', icon: Brain, label: 'Predictions' },
    { id: 'map', path: '/map', icon: Map, label: 'Map' },
    { id: 'reports', path: '/reports', icon: FileText, label: 'Reports' },
    { id: 'settings', path: '/settings', icon: Settings, label: 'Settings' },
  ];

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  return (
    <aside className={`${styles.sidebar} ${isDarkMode ? styles.dark : styles.light}`}>
      {/* Logo */}
      <div className={styles.logoSection}>
        <div className={styles.logoContainer}>
          <div className={styles.logoIcon}>
            <Shield className={styles.shieldIcon} />
          </div>
          <div className={styles.logoText}>
            <div className={styles.logoTitle}>AI Disease Risk</div>
            <div className={styles.logoSubtitle}>Prediction System</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className={styles.navigation}>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <button
              key={item.id}
              onClick={() => handleNavigation(item.path)}
              className={`${styles.menuItem} ${isActive ? styles.active : ''} ${isDarkMode ? styles.darkItem : styles.lightItem}`}
            >
              <Icon className={styles.menuIcon} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className={styles.footer}>
        <div className={styles.syncText}>Last sync: 2 mins ago</div>
      </div>
    </aside>
  );
}

