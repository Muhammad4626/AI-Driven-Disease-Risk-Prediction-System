import React from 'react';
import {
  LayoutDashboard,
  Brain,
  FileText,
  Settings,
  Shield,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useDashboard } from '../../../context/DashboardContext';
import styles from './Sidebar.module.css';

interface SidebarProps {
  isDarkMode?: boolean;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onNavigateToSection: (mode: 'overview' | 'prediction') => void;
}

export function Sidebar({
  isDarkMode = false,
  isCollapsed,
  onToggleCollapse,
  onNavigateToSection,
}: SidebarProps) {
  const { viewMode } = useDashboard();

  const menuItems = [
    { id: 'overview', icon: LayoutDashboard, label: 'Dashboard', mode: 'overview' as const },
    { id: 'prediction', icon: Brain, label: 'Predictions', mode: 'prediction' as const },
    { id: 'reports', icon: FileText, label: 'Reports', mode: undefined },
    { id: 'settings', icon: Settings, label: 'Settings', mode: undefined },
  ];

  const handleMenuClick = (mode: 'overview' | 'prediction' | undefined) => {
    if (!mode) return;
    onNavigateToSection(mode);
  };

  return (
    <aside
      className={`${styles.sidebar} ${isDarkMode ? styles.dark : styles.light} ${
        isCollapsed ? styles.collapsed : ''
      }`}
    >
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
        <button
          type="button"
          className={styles.collapseButton}
          onClick={onToggleCollapse}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className={styles.navigation}>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            (item.mode === 'overview' && viewMode === 'overview') ||
            (item.mode === 'prediction' && viewMode === 'prediction');

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => handleMenuClick(item.mode)}
              className={`${styles.menuItem} ${isActive ? styles.active : ''} ${isDarkMode ? styles.darkItem : styles.lightItem}`}
            >
              <Icon className={styles.menuIcon} />
              {!isCollapsed && <span>{item.label}</span>}
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

