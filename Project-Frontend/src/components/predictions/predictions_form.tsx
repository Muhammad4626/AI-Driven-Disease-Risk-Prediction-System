import React from 'react';
import { Brain } from 'lucide-react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Select } from '../common/Select';
import styles from './PredictionsForm.module.css';

interface PredictionsFormProps {
  formData: {
    district: string;
    rainfall: string;
    population: string;
  };
  onFormDataChange: (field: string, value: string) => void;
  onGenerate: () => void;
  onWeatherData?: () => void;
  isGenerating: boolean;
  isFormValid: boolean;
}

export function PredictionsForm({
  formData,
  onFormDataChange,
  onGenerate,
  onWeatherData,
  isGenerating,
  isFormValid,
}: PredictionsFormProps) {
  const districtOptions = [
    { value: 'sindh-dadu', label: 'Dadu, Sindh' },
    { value: 'sindh-jamshoro', label: 'Jamshoro, Sindh' },
    { value: 'punjab-rajanpur', label: 'Rajanpur, Punjab' },
    { value: 'balochistan-jaffarabad', label: 'Jaffarabad, Balochistan' },
    { value: 'kpk-charsadda', label: 'Charsadda, KPK' },
  ];

  const rainfallOptions = [
    { value: 'none', label: 'None (0mm)' },
    { value: 'light', label: 'Light (1-50mm)' },
    { value: 'moderate', label: 'Moderate (51-100mm)' },
    { value: 'heavy', label: 'Heavy (101-200mm)' },
    { value: 'extreme', label: 'Extreme (200mm+)' },
  ];

  const populationOptions = [
    { value: 'low', label: 'Low (< 100/km²)' },
    { value: 'medium', label: 'Medium (100-500/km²)' },
    { value: 'high', label: 'High (500-1000/km²)' },
    { value: 'very-high', label: 'Very High (> 1000/km²)' },
  ];

  return (
    <Card className={styles.formCard}>
      <div className={styles.header}>
        <div className={styles.iconContainer}>
          <Brain className={styles.icon} />
        </div>
        <h2 className={styles.title}>Input Parameters</h2>
      </div>

      <div className={styles.formFields}>
        <Select
          label="District"
          value={formData.district}
          onChange={(value) => onFormDataChange('district', value)}
          placeholder="Select District..."
          options={districtOptions}
        />

        <Select
          label="Rainfall Level (Last 7 Days)"
          value={formData.rainfall}
          onChange={(value) => onFormDataChange('rainfall', value)}
          placeholder="Select Rainfall Level (Last 7 Days)..."
          options={rainfallOptions}
        />

        <Select
          label="Population Density"
          value={formData.population}
          onChange={(value) => onFormDataChange('population', value)}
          placeholder="Select Population Density..."
          options={populationOptions}
        />

        {onWeatherData && (
          <Button
            onClick={onWeatherData}
            className={styles.weatherButton}
          >
            Weather Data
          </Button>
        )}

        <Button
          onClick={onGenerate}
          disabled={!isFormValid || isGenerating}
        >
          {isGenerating ? 'Generating Prediction...' : 'Generate Prediction'}
        </Button>
      </div>
    </Card>
  );
}

