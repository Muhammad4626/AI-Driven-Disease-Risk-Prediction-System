import React, { useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useDashboard } from '../../context/DashboardContext';
import type { DistrictRiskDataAPI } from './districtRiskData';

export interface TrendChartProps {
  className?: string;
  riskData: DistrictRiskDataAPI | null;
}

export function TrendChart({ className, riskData }: TrendChartProps) {
  const { activeDistrictPCode, selectedDisease } = useDashboard();
  const [trendData, setTrendData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadTrend() {
      if (!riskData || !activeDistrictPCode) {
        setTrendData([]);
        return;
      }

      setLoading(true);
      try {
        const data = await riskData.getWeeklyTrend(activeDistrictPCode, selectedDisease);
        setTrendData(data);
      } catch (err) {
        console.error("Error loading trend data:", err);
        setTrendData([]);
      } finally {
        setLoading(false);
      }
    }

    loadTrend();
  }, [riskData, activeDistrictPCode, selectedDisease]);

  const label = activeDistrictPCode
    ? `Weekly risk trend — District ${activeDistrictPCode}`
    : 'Select a district on the map to see weekly risk trend';

  return (
    <div className={className} style={{ width: '100%', minHeight: 320 }}>
      <h3 className="trendChartTitle" style={{ marginBottom: 8, fontSize: '1rem', fontWeight: 600, color: '#030213' }}>
        {selectedDisease.charAt(0).toUpperCase() + selectedDisease.slice(1)} risk trend
      </h3>

      {loading ? (
        <div style={{ height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6b7280' }}>
          Loading trend...
        </div>
      ) : trendData.length === 0 ? (
        <div
          style={{
            height: 280,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#6b7280',
            fontSize: '0.875rem',
          }}
        >
          {label}
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={trendData} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="week" tick={{ fontSize: 11 }} stroke="#6b7280" />
            <YAxis domain={[0, 50]} tick={{ fontSize: 11 }} stroke="#6b7280" />
            <Tooltip
              formatter={(value: number) => [`${value}%`, 'Risk']}
              contentStyle={{ borderRadius: 8, border: '1px solid #e5e7eb' }}
            />
            <Area
              type="monotone"
              dataKey="risk"
              stroke="#2563eb"
              fill="#93c5fd"
              fillOpacity={0.6}
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}