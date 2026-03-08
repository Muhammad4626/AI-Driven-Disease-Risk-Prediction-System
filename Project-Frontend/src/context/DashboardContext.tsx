import React, {
  createContext,
  useContext,
  useState,
  ReactNode,
} from 'react';

// Diseases the dashboard supports globally
export type DiseaseKey = 'malaria' | 'diarrhea' | 'typhoid';

// section of the unified dashboard that is in focus
export type ViewMode = 'overview' | 'prediction';

export interface ShapValue {
  feature: string;
  importance: number;
}

export interface PredictionData {
  districtPCode: string;
  disease: DiseaseKey;
  riskLevel: 'High' | 'Medium' | 'Low';
  confidence: number;
  nextWeekRisk: number;
  shapValues: ShapValue[];
}

interface DashboardState {
  selectedDisease: DiseaseKey;
  activeDistrictPCode: string | null;
  viewMode: ViewMode;
  predictionData: PredictionData | null;
  setSelectedDisease: (disease: DiseaseKey) => void;
  setActiveDistrictPCode: (pcode: string | null) => void;
  setViewMode: (mode: ViewMode) => void;
  setPredictionData: (data: PredictionData | null) => void;
}

const DashboardContext = createContext<DashboardState | undefined>(undefined);

interface DashboardProviderProps {
  children: ReactNode;
}

export function DashboardProvider({ children }: DashboardProviderProps) {
  const [selectedDisease, setSelectedDisease] = useState<DiseaseKey>('malaria');
  const [activeDistrictPCode, setActiveDistrictPCode] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('overview');
  const [predictionData, setPredictionData] = useState<PredictionData | null>(null);

  const value: DashboardState = {
    selectedDisease,
    activeDistrictPCode,
    viewMode,
    predictionData,
    setSelectedDisease,
    setActiveDistrictPCode,
    setViewMode,
    setPredictionData,
  };

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboard(): DashboardState {
  const ctx = useContext(DashboardContext);
  if (!ctx) {
    throw new Error('useDashboard must be used within a DashboardProvider');
  }
  return ctx;
}

