import React, { useEffect, useState, useCallback } from 'react';
import { Activity, Users } from 'lucide-react';
import { Card } from '../common/Card';
import { ChoroplethMap } from './ChoroplethMap';
import { TrendChart } from './TrendChart';
import { useDashboard } from '../../context/DashboardContext';
import type { DistrictRiskDataAPI } from './districtRiskData';
import { getCumulativeCases } from '../../services/predictionService';
import styles from './DashboardPage.module.css';

interface SummaryCard {
  title: string;
  value: string;
  icon: React.ReactNode;
  color: 'orange' | 'blue';
}

const DISEASES = ['malaria', 'diarrhea', 'typhoid'] as const;

export function DashboardPage() {
  const { selectedDisease, setSelectedDisease } = useDashboard();
  const [riskData, setRiskData] = useState<DistrictRiskDataAPI | null>(null);
  const onMapDataReady = useCallback((data: DistrictRiskDataAPI) => setRiskData(data), []);

  const [totalCases, setTotalCases] = useState<number | null>(null);
  const [isCasesLoading, setIsCasesLoading] = useState(false);

  useEffect(() => {
    let isCancelled = false;
    async function loadCases() {
      setIsCasesLoading(true);
      try {
        const diseaseParam =
          selectedDisease === 'diarrhea' ? 'diarrhea' : selectedDisease;
        const resp = await getCumulativeCases(diseaseParam);
        if (!isCancelled) setTotalCases(Number(resp.total_cases) || 0);
      } catch {
        if (!isCancelled) setTotalCases(null);
      } finally {
        if (!isCancelled) setIsCasesLoading(false);
      }
    }
    loadCases();
    return () => {
      isCancelled = true;
    };
  }, [selectedDisease]);

  const formatNumber = (n: number) => n.toLocaleString('en-US');

  const summaryCards: SummaryCard[] = [
    {
      title: 'Active Cases',
      value: isCasesLoading ? 'Loading…' : totalCases != null ? formatNumber(totalCases) : '—',
      icon: <Activity className={styles.icon} />,
      color: 'orange',
    },
    {
      title: 'Monitored Areas',
      value: '147',
      icon: <Users className={styles.icon} />,
      color: 'blue',
    },
  ];

  const getCurrentDateTime = () => {
    const now = new Date();
    const options: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Karachi',
      timeZoneName: 'short',
    };
    return now.toLocaleString('en-US', options).replace(',', ' -');
  };

  return (
    <div className={styles.contentWrapper}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <h1 className={styles.pageTitle}>Disease Risk Dashboard</h1>
          <p className={styles.pageSubtitle}>
            Real-time monitoring and predictions for post-flood areas
          </p>
        </div>
        <div className={styles.lastUpdated}>
          Last Updated {getCurrentDateTime()}
        </div>
      </div>

      {/* Summary Cards */}
      <div className={styles.summaryGrid}>
        {summaryCards.map((card, index) => (
          <Card key={index} className={`${styles.summaryCard} ${styles[card.color]}`}>
            <div className={styles.cardHeader}>
              <div className={`${styles.iconContainer} ${styles[`${card.color}Icon`]}`}>
                {card.icon}
              </div>
            </div>
            <div className={styles.cardContent}>
              <div className={styles.cardValue}>{card.value}</div>
              <div className={styles.cardTitle}>{card.title}</div>
            </div>
          </Card>
        ))}
      </div>

      {/* Disease selector */}
      <div className={styles.diseaseTabs}>
        {DISEASES.map((d) => (
          <button
            key={d}
            type="button"
            className={`${styles.diseaseTab} ${selectedDisease === d ? styles.active : ''}`}
            onClick={() => setSelectedDisease(d)}
          >
            {d.charAt(0).toUpperCase() + d.slice(1)}
          </button>
        ))}
      </div>

      {/* Map (left) + Trend chart (right) */}
      <div className={styles.mapChartGrid}>
        <div className={styles.mapPanel}>
          <ChoroplethMap onDataReady={onMapDataReady} />
        </div>
        <div className={styles.chartPanel}>
          <TrendChart riskData={riskData} />
        </div>
      </div>
    </div>
  );
}

