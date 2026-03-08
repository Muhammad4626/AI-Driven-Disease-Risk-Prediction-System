import React, { useMemo } from 'react';
import { Brain } from 'lucide-react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Select } from '../common/Select';
import pakAdmin2Geo from '../../assets/map_boundaries/pak_admin2_em.json';
import styles from './PredictionsForm.module.css';

type DistrictFeature = {
  id?: string | number;
  properties?: {
    adm2_pcode?: string;
    adm2_en?: string;
    adm2name?: string;
    name?: string;
  } & Record<string, unknown>;
};

type DistrictGeoJSON = {
  features?: DistrictFeature[];
};

interface PredictionsFormProps {
  formData: {
    district: string;
    week: string;
    year: string;
    malariaCases: string;
    acuteDiarrheaCases: string;
    typhoidCases: string;
  };
  onFormDataChange: (field: string, value: string) => void;
  onGenerate: () => void;
  isGenerating: boolean;
  isFormValid: boolean;
}

export function PredictionsForm({
  formData,
  onFormDataChange,
  onGenerate,
  isGenerating,
  isFormValid,
}: PredictionsFormProps) {
  const districtOptions = useMemo(() => {
    const raw = pakAdmin2Geo as DistrictGeoJSON;
    const features = raw.features ?? [];

    return features.map((f, index) => {
      const props = f.properties ?? {};
      const pcode =
        props.adm2_pcode ??
        (f.id != null ? String(f.id) : `DIST_${index}`);

      let label =
        (props.adm2_en as string | undefined) ??
        (props.adm2name as string | undefined) ??
        (props.name as string | undefined);

      if (!label) {
        const nameKey = Object.keys(props).find((k) =>
          k.toLowerCase().includes('name')
        );
        const maybeName =
          nameKey != null ? (props as Record<string, unknown>)[nameKey] : null;
        if (typeof maybeName === 'string' && maybeName.trim().length > 0) {
          label = maybeName;
        }
      }

      if (!label) {
        label = pcode;
      }

      return {
        value: pcode,
        label,
      };
    });
  }, []);

  const yearOptions = useMemo(() => {
    const currentYear = new Date().getFullYear();
    const startYear = currentYear - 10;
    const endYear = currentYear + 5;
    const years = [];
    for (let y = startYear; y <= endYear; y++) {
      years.push({ value: String(y), label: String(y) });
    }
    return years;
  }, []);

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
          label="Year"
          value={formData.year}
          onChange={(value) => onFormDataChange('year', value)}
          placeholder="Select Year..."
          options={yearOptions}
        />

        <div className={styles.inputGroup}>
          <label className={styles.label}>Week Number</label>
          <input
            type="number"
            min={1}
            max={52}
            value={formData.week}
            onChange={(e) => onFormDataChange('week', e.target.value)}
            className={styles.input}
            placeholder="Enter week number (1-52)"
          />
        </div>

        <div className={styles.inputGroup}>
          <label className={styles.label}>Malaria Cases</label>
          <input
            type="number"
            min={0}
            value={formData.malariaCases}
            onChange={(e) => onFormDataChange('malariaCases', e.target.value)}
            className={styles.input}
            placeholder="Enter malaria cases"
          />
        </div>

        <div className={styles.inputGroup}>
          <label className={styles.label}>Acute Diarrhea Cases</label>
          <input
            type="number"
            min={0}
            value={formData.acuteDiarrheaCases}
            onChange={(e) =>
              onFormDataChange('acuteDiarrheaCases', e.target.value)
            }
            className={styles.input}
            placeholder="Enter acute diarrhea cases"
          />
        </div>

        <div className={styles.inputGroup}>
          <label className={styles.label}>Typhoid Cases</label>
          <input
            type="number"
            min={0}
            value={formData.typhoidCases}
            onChange={(e) => onFormDataChange('typhoidCases', e.target.value)}
            className={styles.input}
            placeholder="Enter typhoid cases"
          />
        </div>

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

