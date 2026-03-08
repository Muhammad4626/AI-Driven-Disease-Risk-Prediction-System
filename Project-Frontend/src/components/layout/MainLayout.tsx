import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Sidebar } from './sidebar';
import { useDashboard } from '../../context/DashboardContext';
import { DashboardPage } from '../dashboard';
import { PredictionsPage } from '../predictions';
import styles from './MainLayout.module.css';

const SECTION_OVERVIEW = 'section-overview';
const SECTION_PREDICTION = 'section-prediction';

export function MainLayout() {
  const { setViewMode } = useDashboard();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const mainRef = useRef<HTMLElement>(null);

  const scrollToSection = useCallback(
    (mode: 'overview' | 'prediction') => {
      setViewMode(mode);
      const id = mode === 'overview' ? SECTION_OVERVIEW : SECTION_PREDICTION;
      const el = document.getElementById(id);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    },
    [setViewMode]
  );

  useEffect(() => {
    const main = mainRef.current;
    if (!main) return;

    const overviewEl = document.getElementById(SECTION_OVERVIEW);
    const predictionEl = document.getElementById(SECTION_PREDICTION);
    if (!overviewEl || !predictionEl) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          const ratio = entry.intersectionRatio;
          if (ratio < 0.2) continue;
          const mode = entry.target.id === SECTION_OVERVIEW ? 'overview' : 'prediction';
          setViewMode(mode);
        }
      },
      { root: main, threshold: [0.2, 0.5, 1], rootMargin: '-20% 0px -60% 0px' }
    );

    observer.observe(overviewEl);
    observer.observe(predictionEl);
    return () => observer.disconnect();
  }, [setViewMode]);

  return (
    <div className={styles.layout}>
      <Sidebar
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
        onNavigateToSection={scrollToSection}
      />
      <main
        ref={mainRef}
        className={`${styles.main} ${isSidebarCollapsed ? styles.mainCollapsed : ''}`}
      >
        <div className={styles.scrollContent}>
          <section id={SECTION_OVERVIEW} className={styles.section}>
            <DashboardPage />
          </section>
          <section id={SECTION_PREDICTION} className={styles.section}>
            <PredictionsPage />
          </section>
        </div>
      </main>
    </div>
  );
}

