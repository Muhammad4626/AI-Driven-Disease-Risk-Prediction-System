import React, { useState } from 'react';
import { Brain, AlertCircle, CheckCircle, TrendingUp } from 'lucide-react';
import { Sidebar } from '../layout/sidebar';
import { Card } from '../common/Card';
import { PredictionsForm } from './predictions_form';
import styles from './PredictionsPage.module.css';

interface Disease {
  name: string;
  probability: number;
  cases: string;
}

interface Prediction {
  riskLevel: 'High' | 'Medium' | 'Low';
  confidence: number;
  diseases: Disease[];
  recommendations: string[];
}

export function PredictionsPage() {
  const [formData, setFormData] = useState({
    district: '',
    rainfall: '',
    population: '',
  });
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleFormDataChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleGenerate = () => {
    setIsGenerating(true);

    // Simulate API call
    setTimeout(() => {
      setPrediction({
        riskLevel: 'High',
        confidence: 87,
        diseases: [
          { name: 'Cholera', probability: 78, cases: '1,200-1,800' },
          { name: 'Typhoid', probability: 65, cases: '600-900' },
          { name: 'Hepatitis A', probability: 52, cases: '400-600' },
        ],
        recommendations: [
          'Immediate water purification interventions required',
          'Deploy mobile health units to affected areas',
          'Distribute oral rehydration salts (ORS) packets',
          'Conduct health awareness campaigns',
          'Monitor water sources for contamination daily',
        ],
      });
      setIsGenerating(false);
    }, 1500);
  };

  const handleWeatherData = () => {
    // TODO: Implement weather data functionality
    console.log('Weather Data button clicked');
  };

  const isFormValid = Object.values(formData).every((val) => val !== '');

  const getRiskLevelStyles = (riskLevel: string) => {
    switch (riskLevel) {
      case 'High':
        return {
          bg: styles.riskHighBg,
          text: styles.riskHighText,
          icon: styles.riskHighIcon,
        };
      case 'Medium':
        return {
          bg: styles.riskMediumBg,
          text: styles.riskMediumText,
          icon: styles.riskMediumIcon,
        };
      default:
        return {
          bg: styles.riskLowBg,
          text: styles.riskLowText,
          icon: styles.riskLowIcon,
        };
    }
  };

  const getDiseaseBarColor = (probability: number) => {
    if (probability > 70) return styles.barRed;
    if (probability > 50) return styles.barOrange;
    return styles.barYellow;
  };

  return (
    <div className={styles.container}>
      <Sidebar />
      
      <div className={styles.mainContent}>
        <div className={styles.contentWrapper}>
          {/* Header */}
          <div className={styles.header}>
            <h1 className={styles.pageTitle}>Disease Risk Prediction</h1>
            <p className={styles.pageSubtitle}>
              Generate AI-powered predictions based on environmental and health parameters
            </p>
          </div>

          <div className={styles.grid}>
            {/* Input Form */}
            <PredictionsForm
              formData={formData}
              onFormDataChange={handleFormDataChange}
              onGenerate={handleGenerate}
              onWeatherData={handleWeatherData}
              isGenerating={isGenerating}
              isFormValid={isFormValid}
            />

            {/* Results */}
            <div className={styles.resultsSection}>
              {prediction ? (
                <>
                  {/* Risk Level Card */}
                  <Card className={styles.riskCard}>
                    <h2 className={styles.resultsTitle}>Prediction Results</h2>

                    <div className={`${styles.riskLevelBox} ${getRiskLevelStyles(prediction.riskLevel).bg}`}>
                      <div className={styles.riskLevelHeader}>
                        <span className={styles.riskLabel}>Risk Level</span>
                        <AlertCircle className={`${styles.riskIcon} ${getRiskLevelStyles(prediction.riskLevel).icon}`} />
                      </div>
                      <div className={`${styles.riskLevelValue} ${getRiskLevelStyles(prediction.riskLevel).text}`}>
                        {prediction.riskLevel}
                      </div>
                    </div>

                    <div className={styles.confidenceBox}>
                      <span className={styles.confidenceLabel}>Confidence Score</span>
                      <div className={styles.confidenceValue}>
                        <TrendingUp className={styles.trendingIcon} />
                        <span>{prediction.confidence}%</span>
                      </div>
                    </div>
                  </Card>

                  {/* Disease Probabilities */}
                  <Card className={styles.diseaseCard}>
                    <h3 className={styles.cardTitle}>Disease Probabilities</h3>
                    <div className={styles.diseaseList}>
                      {prediction.diseases.map((disease, index) => (
                        <div key={index} className={styles.diseaseItem}>
                          <div className={styles.diseaseHeader}>
                            <span className={styles.diseaseName}>{disease.name}</span>
                            <span className={styles.diseaseProbability}>{disease.probability}%</span>
                          </div>
                          <div className={styles.progressBar}>
                            <div
                              className={`${styles.progressFill} ${getDiseaseBarColor(disease.probability)}`}
                              style={{ width: `${disease.probability}%` }}
                            />
                          </div>
                          <div className={styles.diseaseCases}>
                            Estimated cases: {disease.cases}
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>

                  {/* Recommendations */}
                  <Card className={styles.recommendationsCard}>
                    <h3 className={styles.cardTitle}>Preventive Measures</h3>
                    <div className={styles.recommendationsList}>
                      {prediction.recommendations.map((rec, index) => (
                        <div key={index} className={styles.recommendationItem}>
                          <CheckCircle className={styles.checkIcon} />
                          <span>{rec}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                </>
              ) : (
                <Card className={styles.emptyState}>
                  <div className={styles.emptyIconContainer}>
                    <Brain className={styles.emptyIcon} />
                  </div>
                  <h3 className={styles.emptyTitle}>No Prediction Yet</h3>
                  <p className={styles.emptyText}>
                    Fill in all parameters and click &apos;Generate Prediction&apos; to see AI-powered risk assessment
                  </p>
                </Card>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

