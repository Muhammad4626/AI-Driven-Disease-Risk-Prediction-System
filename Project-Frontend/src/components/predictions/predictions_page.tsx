import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Brain, AlertCircle, CheckCircle, TrendingUp } from 'lucide-react';
import { Card } from '../common/Card';
import { PredictionsForm } from './predictions_form';
import { DiseaseExplanations, getPrediction } from '../../services/predictionService';
import styles from './PredictionsPage.module.css';

interface Disease {
  name: string;
  probability: number;
  cases: string;
}

interface Prediction {
  riskLevel: 'High' | 'Medium' | 'Low';
  // confidence: number;
  diseases: Disease[];
  recommendations: string[];
  explanations?: DiseaseExplanations;
}

export function PredictionsPage() {
  const [formData, setFormData] = useState({
    district: '',
    week: '',
    year: '',
    malariaCases: '',
    acuteDiarrheaCases: '',
    typhoidCases: '',
  });
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shapReady, setShapReady] = useState(false);
  const shapLoadedIdsRef = useRef<Record<string, true>>({});
  const [shapLoadedCount, setShapLoadedCount] = useState(0);

  const expectedShapImageCount = useMemo(() => {
    if (!prediction?.explanations) return 0;
    return 6;
  }, [prediction?.explanations]);

  const markShapImageLoaded = (id: string) => {
    if (shapLoadedIdsRef.current[id]) return;
    shapLoadedIdsRef.current[id] = true;
    setShapLoadedCount((c) => c + 1);
  };

  const handleFormDataChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleGenerate = async () => {
    setError(null);
    setIsGenerating(true);
    setPrediction(null);
    setShapReady(false);
    shapLoadedIdsRef.current = {};
    setShapLoadedCount(0);

    const yearNum = Number(formData.year);
    const weekNum = Number(formData.week);

    if (!formData.district || Number.isNaN(yearNum) || Number.isNaN(weekNum)) {
      setIsGenerating(false);
      setError('Please provide a valid district, year, and week number.');
      return;
    }

    try {
      const resp = await getPrediction({
        district_name: formData.district,
        year: yearNum,
        week_number: weekNum,
      });

      // Model outputs are already "cases per 10,000"
      const malariaRate = resp.predictions.malaria_risk_next_week;
      const adRate = resp.predictions.ad_risk_next_week;
      const typhoidRate = resp.predictions.typhoid_risk_next_week;

      const maxRisk = Math.max(malariaRate, adRate, typhoidRate);
      let riskLevel: Prediction['riskLevel'] = 'Low';
      if (maxRisk >= 60) riskLevel = 'High';
      else if (maxRisk >= 30) riskLevel = 'Medium';

      // const confidence = Math.round((malariaRate + adRate + typhoidRate) / 3);

      setPrediction({
        riskLevel,
        diseases: [
          { name: 'Malaria', probability: malariaRate, cases: String(malariaRate) },
          { name: 'Acute Diarrhea', probability: adRate, cases: String(adRate) },
          { name: 'Typhoid', probability: typhoidRate, cases: String(typhoidRate) },
        ],
        recommendations: [
          'Increase surveillance and reporting in high-risk districts.',
          'Prepare medical supplies and staff deployment for the coming week.',
          'Prioritize water, sanitation, and hygiene (WASH) interventions.',
        ],
        explanations: resp.predictions.explanations,
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Failed to fetch prediction.';
      setError(msg);
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    if (!shapReady && expectedShapImageCount > 0 && shapLoadedCount >= expectedShapImageCount) {
      // All images have either loaded successfully or errored.
      // We only reveal the SHAP section after this point.
      setShapReady(true);
    }
  }, [expectedShapImageCount, shapLoadedCount, shapReady]);

  const isFormValid = Boolean(formData.district && formData.year && formData.week);

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
          isGenerating={isGenerating}
          isFormValid={isFormValid}
        />

        {/* Results */}
        <div className={styles.resultsSection}>
          {error && (
            <Card className={styles.errorCard}>
              <div className={styles.errorContent}>
                <AlertCircle className={styles.errorIcon} />
                <div>
                  <h3 className={styles.errorTitle}>Prediction Error</h3>
                  <p className={styles.errorMessage}>{error}</p>
                </div>
              </div>
            </Card>
          )}
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

                    {/* <div className={styles.confidenceBox}>
                      <span className={styles.confidenceLabel}>Confidence Score</span>
                      <div className={styles.confidenceValue}>
                        <TrendingUp className={styles.trendingIcon} />
                        <span>{prediction.confidence}%</span>  
                      </div>
                    </div> */}
                  </Card>

                  {/* Disease Probabilities */}
                  <Card className={styles.diseaseCard}>
                    <h3 className={styles.cardTitle}>Disease Probabilities</h3>
                    <div className={styles.diseaseList}>
                      {prediction.diseases.map((disease, index) => (
                        <div key={index} className={styles.diseaseItem}>
                          <div className={styles.diseaseHeader}>
                            <span className={styles.diseaseName}>{disease.name}</span>
                            <span className={styles.diseaseProbability}>
                              {Number.isFinite(disease.probability) ? disease.probability.toFixed(2) : '0.00'}
                            </span>
                          </div>
                          <div className={styles.progressBar}>
                            <div
                              className={`${styles.progressFill} ${getDiseaseBarColor(disease.probability)}`}
                              style={{
                                width: `${Math.max(0, Math.min(100, Math.round(disease.probability)))}%`,
                              }}
                            />
                          </div>
                          <div className={styles.diseaseCases}>
                            Cases per 10,000: {disease.cases}
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>

                  {/* Recommendations */}
                  {/* <Card className={styles.recommendationsCard}>
                    <h3 className={styles.cardTitle}>Preventive Measures</h3>
                    <div className={styles.recommendationsList}>
                      {prediction.recommendations.map((rec, index) => (
                        <div key={index} className={styles.recommendationItem}>
                          <CheckCircle className={styles.checkIcon} />
                          <span>{rec}</span>
                        </div>
                      ))}
                    </div>
                  </Card> */}
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

      {prediction?.explanations && (
        <div className={styles.shapFullWidthSection}>
          <Card className={styles.shapCard}>
            {!shapReady ? (
              <div className={styles.shapLoading}>
                <h3 className={styles.cardTitle}>SHAP Explanations</h3>
                <p className={styles.shapLoadingText}>
                  Loading explanation plots… ({Math.min(shapLoadedCount, expectedShapImageCount)}/{expectedShapImageCount})
                </p>

                <div className={styles.shapPreloadGrid} aria-hidden="true">
                  <img
                    src={prediction.explanations.malaria.waterfall_plot}
                    alt=""
                    className={styles.shapImageHidden}
                    onLoad={() => markShapImageLoaded('malaria-waterfall')}
                    onError={() => markShapImageLoaded('malaria-waterfall')}
                  />
                  <img
                    src={prediction.explanations.malaria.bar_plot}
                    alt=""
                    className={styles.shapImageHidden}
                    onLoad={() => markShapImageLoaded('malaria-bar')}
                    onError={() => markShapImageLoaded('malaria-bar')}
                  />
                  <img
                    src={prediction.explanations.ad.waterfall_plot}
                    alt=""
                    className={styles.shapImageHidden}
                    onLoad={() => markShapImageLoaded('ad-waterfall')}
                    onError={() => markShapImageLoaded('ad-waterfall')}
                  />
                  <img
                    src={prediction.explanations.ad.bar_plot}
                    alt=""
                    className={styles.shapImageHidden}
                    onLoad={() => markShapImageLoaded('ad-bar')}
                    onError={() => markShapImageLoaded('ad-bar')}
                  />
                  <img
                    src={prediction.explanations.typhoid.waterfall_plot}
                    alt=""
                    className={styles.shapImageHidden}
                    onLoad={() => markShapImageLoaded('typhoid-waterfall')}
                    onError={() => markShapImageLoaded('typhoid-waterfall')}
                  />
                  <img
                    src={prediction.explanations.typhoid.bar_plot}
                    alt=""
                    className={styles.shapImageHidden}
                    onLoad={() => markShapImageLoaded('typhoid-bar')}
                    onError={() => markShapImageLoaded('typhoid-bar')}
                  />
                </div>
              </div>
            ) : (
              <details className={styles.shapDetails}>
                <summary className={styles.shapSummary}>
                  <span className={styles.shapTitle}>SHAP Explanations</span>
                  <span className={styles.shapSummaryHint}>Click to expand</span>
                </summary>

                <div className={styles.shapBody}>
                  <div className={styles.shapDiseaseSection}>
                    <h4 className={styles.shapDiseaseTitle}>Malaria</h4>
                    <div className={styles.shapImagesGrid}>
                      <figure className={styles.shapFigure}>
                        <figcaption className={styles.shapCaption}>Waterfall plot</figcaption>
                        <img
                          src={prediction.explanations.malaria.waterfall_plot}
                          alt="SHAP waterfall plot for Malaria"
                          className={styles.shapImage}
                          loading="lazy"
                        />
                      </figure>
                      <figure className={styles.shapFigure}>
                        <figcaption className={styles.shapCaption}>Bar plot</figcaption>
                        <img
                          src={prediction.explanations.malaria.bar_plot}
                          alt="SHAP bar plot for Malaria"
                          className={styles.shapImage}
                          loading="lazy"
                        />
                      </figure>
                    </div>
                  </div>

                  <div className={styles.shapDiseaseSection}>
                    <h4 className={styles.shapDiseaseTitle}>Acute Diarrhea</h4>
                    <div className={styles.shapImagesGrid}>
                      <figure className={styles.shapFigure}>
                        <figcaption className={styles.shapCaption}>Waterfall plot</figcaption>
                        <img
                          src={prediction.explanations.ad.waterfall_plot}
                          alt="SHAP waterfall plot for Acute Diarrhea"
                          className={styles.shapImage}
                          loading="lazy"
                        />
                      </figure>
                      <figure className={styles.shapFigure}>
                        <figcaption className={styles.shapCaption}>Bar plot</figcaption>
                        <img
                          src={prediction.explanations.ad.bar_plot}
                          alt="SHAP bar plot for Acute Diarrhea"
                          className={styles.shapImage}
                          loading="lazy"
                        />
                      </figure>
                    </div>
                  </div>

                  <div className={styles.shapDiseaseSection}>
                    <h4 className={styles.shapDiseaseTitle}>Typhoid</h4>
                    <div className={styles.shapImagesGrid}>
                      <figure className={styles.shapFigure}>
                        <figcaption className={styles.shapCaption}>Waterfall plot</figcaption>
                        <img
                          src={prediction.explanations.typhoid.waterfall_plot}
                          alt="SHAP waterfall plot for Typhoid"
                          className={styles.shapImage}
                          loading="lazy"
                        />
                      </figure>
                      <figure className={styles.shapFigure}>
                        <figcaption className={styles.shapCaption}>Bar plot</figcaption>
                        <img
                          src={prediction.explanations.typhoid.bar_plot}
                          alt="SHAP bar plot for Typhoid"
                          className={styles.shapImage}
                          loading="lazy"
                        />
                      </figure>
                    </div>
                  </div>
                </div>
              </details>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

