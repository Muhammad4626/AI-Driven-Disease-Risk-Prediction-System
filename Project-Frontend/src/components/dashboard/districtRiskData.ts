import type { DiseaseKey } from '../../context/DashboardContext';

export interface WeeklyTrendPoint {
  week: string;
  risk: number;
}

export interface DistrictRiskDataAPI {
  getRiskScore: (pcode: string, disease: DiseaseKey) => number;
  getWeeklyTrend: (pcode: string, disease: DiseaseKey) => WeeklyTrendPoint[];
}

/**
 * Deterministic pseudo-random in [0,1] from string seed.
 */
function seeded(seed: string): number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) {
    h = Math.imul(31, h) + seed.charCodeAt(i) | 0;
  }
  return (Math.abs(h) % 1000) / 1000;
}

/**
 * Build risk score (0–100) and weekly trend for each district.
 * Uses deterministic mock data keyed by pcode and disease so map and chart stay in sync.
 */
export function buildDistrictRiskData(pcodes: string[]): DistrictRiskDataAPI {
  const riskByKey: Record<string, number> = {};
  const trendByKey: Record<string, WeeklyTrendPoint[]> = {};

  const weeks = 8;
  const weekLabels: string[] = [];
  const now = new Date();
  for (let i = weeks - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - 7 * i);
    weekLabels.push(d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' }));
  }

  const diseases: DiseaseKey[] = ['malaria', 'diarrhea', 'typhoid'];
  for (const pcode of pcodes) {
    for (const disease of diseases) {
      const key = `${pcode}:${disease}`;
      const r = seeded(key);
      riskByKey[key] = Math.round(20 + r * 80);
      const trend: WeeklyTrendPoint[] = [];
      let v = 15 + seeded(key + ':0') * 70;
      for (let w = 0; w < weeks; w++) {
        v = Math.max(5, Math.min(95, v + (seeded(key + ':' + w) - 0.5) * 20));
        trend.push({ week: weekLabels[w], risk: Math.round(v) });
      }
      trendByKey[key] = trend;
    }
  }

  return {
    getRiskScore(pcode: string, disease: DiseaseKey): number {
      const key = `${pcode}:${disease}`;
      return riskByKey[key] ?? 50;
    },
    getWeeklyTrend(pcode: string, disease: DiseaseKey): WeeklyTrendPoint[] {
      const key = `${pcode}:${disease}`;
      return trendByKey[key] ?? weekLabels.map((week) => ({ week, risk: 50 }));
    },
  };
}
