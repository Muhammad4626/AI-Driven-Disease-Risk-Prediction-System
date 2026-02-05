import React from 'react';
import { AlertTriangle, Activity, Users, Droplet, TrendingUp, TrendingDown } from 'lucide-react';
import { Sidebar } from '../layout/sidebar';
import { Card } from '../common/Card';
import styles from './DashboardPage.module.css';

interface SummaryCard {
  title: string;
  value: string;
  change: string;
  changeType: 'increase' | 'decrease';
  icon: React.ReactNode;
  color: 'red' | 'orange' | 'blue' | 'green';
}

export function DashboardPage() {

  const summaryCards: SummaryCard[] = [
    {
      title: 'Total Alerts',
      value: '23',
      change: '+12%',
      changeType: 'increase',
      icon: <AlertTriangle className={styles.icon} />,
      color: 'red',
    },
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
    <div className={styles.container}>
      <Sidebar />
      
      <div className={styles.mainContent}>
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
        </div>
      </div>
    </div>
  );
}

