import React, { useState, useCallback } from 'react';
import { AlertTriangle, Activity, Users, Droplet, TrendingUp, TrendingDown } from 'lucide-react';
import { Card } from '../common/Card';
import { ChoroplethMap } from './ChoroplethMap';
import { TrendChart } from './TrendChart';
import { useDashboard } from '../../context/DashboardContext';
import type { DistrictRiskDataAPI } from './districtRiskData';
import styles from './DashboardPage.module.css';

interface SummaryCard {
  title: string;
  value: string;
  change: string;
  changeType: 'increase' | 'decrease';
  icon: React.ReactNode;
  color: 'red' | 'orange' | 'blue' | 'green';
}

const DISEASES = ['malaria', 'diarrhea', 'typhoid'] as const;

export function DashboardPage() {
  const { selectedDisease, setSelectedDisease } = useDashboard();
  const [riskData, setRiskData] = useState<DistrictRiskDataAPI | null>(null);
  const onMapDataReady = useCallback((data: DistrictRiskDataAPI) => setRiskData(data), []);

  const summaryCards: SummaryCard[] = [
    {
      title: 'Active Cases',
      value: '5,523',
      change: '+8%',
      changeType: 'increase',
      icon: <Activity className={styles.icon} />,
      color: 'orange',
    },
    {
      title: 'Monitored Areas',
      value: '147',
      change: '+3',
      changeType: 'increase',
      icon: <Users className={styles.icon} />,
      color: 'blue',
    },
    {
      title: 'Water Quality',
      value: '64%',
      change: '-5%',
      changeType: 'decrease',
      icon: <Droplet className={styles.icon} />,
      color: 'green',
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
              <div className={`${styles.changeIndicator} ${styles[card.changeType]}`}>
                {card.changeType === 'increase' ? (
                  <TrendingUp className={styles.trendIcon} />
                ) : (
                  <TrendingDown className={styles.trendIcon} />
                )}
                <span>{card.change}</span>
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

