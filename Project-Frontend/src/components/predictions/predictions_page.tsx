import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Brain, AlertCircle, Download } from 'lucide-react';
import { Card } from '../common/Card';
import { PredictionsForm } from './predictions_form';
import { getPrediction } from '../../services/predictionService';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import styles from './PredictionsPage.module.css';

interface Disease {
  name: string;
  probability: number;
  cases: string;
}

interface Prediction {
  riskLevel: 'High' | 'Medium' | 'Low';
  diseases: Disease[];
  recommendations: string[];
  local_explanations?: any;      // Updated
  global_explanations?: any;     // Updated
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
  const [isDownloading, setIsDownloading] = useState(false);
  const [isShapExpanded, setIsShapExpanded] = useState(false);
  const [isPdfMode, setIsPdfMode] = useState(false);
  const reportRef = useRef<HTMLDivElement | null>(null);

  const expectedShapImageCount = useMemo(() => {
    if (!prediction) return 0;
    return 12; // 6 local + 6 global
  }, [prediction]);

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
      const malariaRate = resp.predictions.malaria_risk_next_week || 0;
      const adRate = resp.predictions.ad_risk_next_week || 0;
      const typhoidRate = resp.predictions.typhoid_risk_next_week || 0;

      const maxRisk = Math.max(malariaRate, adRate, typhoidRate);
      let riskLevel: Prediction['riskLevel'] = 'Low';
      if (maxRisk >= 60) riskLevel = 'High';
      else if (maxRisk >= 30) riskLevel = 'Medium';

      setPrediction({
        riskLevel,
        diseases: [
          { name: 'Malaria', probability: malariaRate, cases: malariaRate.toFixed(2) },
          { name: 'Acute Diarrhea', probability: adRate, cases: adRate.toFixed(2) },
          { name: 'Typhoid', probability: typhoidRate, cases: typhoidRate.toFixed(2) },
        ],
        recommendations: [
          'Increase surveillance and reporting in high-risk districts.',
          'Prepare medical supplies and staff deployment for the coming week.',
          'Prioritize water, sanitation, and hygiene (WASH) interventions.',
        ],
        local_explanations: resp.predictions.local_explanations,
        global_explanations: resp.predictions.global_explanations,
      });
      setIsShapExpanded(false);
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Failed to fetch prediction.';
      setError(msg);
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadReportPdf = async () => {
    if (!reportRef.current || !prediction) return;
    setIsDownloading(true);

    const prevExpanded = isShapExpanded;
    const prevPdfMode = isPdfMode;
    setIsPdfMode(true);
    if (!shapReady) {
      // still allow PDF without SHAP, but don't force-expand
    } else {
      setIsShapExpanded(true);
      await new Promise((r) => setTimeout(r, 50));
    }

    try {
      await new Promise((r) => setTimeout(r, 50));
      const canvas = await html2canvas(reportRef.current, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff',
        windowWidth: reportRef.current.scrollWidth,
      });
      const imgData = canvas.toDataURL('image/png');

      const pdf = new jsPDF('p', 'mm', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();

      const imgWidth = pageWidth;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      let heightLeft = imgHeight;
      let position = 0;

      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;

      while (heightLeft > 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }

      const districtSafe = (formData.district || 'district').replace(/[^\w\-]+/g, '_');
      pdf.save(`prediction_report_${districtSafe}_week_${formData.week || 'NA'}_${formData.year || 'NA'}.pdf`);
    } finally {
      if (shapReady) setIsShapExpanded(prevExpanded);
      setIsPdfMode(prevPdfMode);
      setIsDownloading(false);
    }
  };

  useEffect(() => {
    if (!shapReady && expectedShapImageCount > 0 && shapLoadedCount >= expectedShapImageCount) {
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
    <div className={styles.contentWrapper} ref={reportRef}>
      {/* Header */}
      <div className={styles.header}>
        <h1 className={styles.pageTitle}>Disease Risk Prediction</h1>
        <p className={styles.pageSubtitle}>
          Generate AI-powered predictions based on environmental and health parameters
        </p>
      </div>

      <div className={styles.grid}>
        {/* Input Form */}
        {!isPdfMode && (
          <PredictionsForm
            formData={formData}
            onFormDataChange={handleFormDataChange}
            onGenerate={handleGenerate}
            isGenerating={isGenerating}
            isFormValid={isFormValid}
          />
        )}

        {/* Results */}
        <div className={styles.resultsSection} style={isPdfMode ? { gridColumn: '1 / -1' } : undefined}>
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

                <div style={{ marginTop: 12, display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    type="button"
                    onClick={downloadReportPdf}
                    disabled={isDownloading}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '10px 12px',
                      borderRadius: 10,
                      border: '1px solid #e5e7eb',
                      background: '#ffffff',
                      cursor: isDownloading ? 'not-allowed' : 'pointer',
                      fontWeight: 600,
                    }}
                    aria-label="Download prediction report as PDF"
                    title={shapReady ? 'Download PDF report' : 'Download PDF report (SHAP still loading)'}
                  >
                    <Download size={16} />
                    {isDownloading ? 'Preparing PDF…' : 'Download report (PDF)'}
                  </button>
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
            </>
          ) : (
            <Card className={styles.emptyState}>
              <div className={styles.emptyIconContainer}>
                <Brain className={styles.emptyIcon} />
              </div>
              <h3 className={styles.emptyTitle}>No Prediction Yet</h3>
              <p className={styles.emptyText}>
                Fill in all parameters and click 'Generate Prediction' to see AI-powered risk assessment
              </p>
            </Card>
          )}

        </div>
      </div>

      {/* SHAP Explanations Section */}
      <div id="section-reports" className={styles.shapFullWidthSection} style={{ scrollMarginTop: 16 }}>
        <Card className={styles.shapCard}>
          {!prediction ? (
            <div className={styles.shapLoading}>
              <h3 className={styles.cardTitle}>SHAP Explanations</h3>
              <p className={styles.shapLoadingText}>Generate a prediction to view the report and SHAP explanations.</p>
            </div>
          ) : !shapReady ? (
            <div className={styles.shapLoading}>
              <h3 className={styles.cardTitle}>SHAP Explanations</h3>
              <p className={styles.shapLoadingText}>
                Loading explanation plots… ({Math.min(shapLoadedCount, expectedShapImageCount)}/{expectedShapImageCount})
              </p>

              <div className={styles.shapPreloadGrid} aria-hidden="true">
                {/* Preload Local + Global images */}
                {['malaria', 'ad', 'typhoid'].map((key) => {
                  const localData = prediction.local_explanations?.[key];
                  const globalData = prediction.global_explanations?.[key];
                  return (
                    <React.Fragment key={key}>
                      {localData && (
                        <>
                          <img
                            src={`data:image/png;base64,${localData.waterfall}`}
                            alt=""
                            className={styles.shapImageHidden}
                            onLoad={() => markShapImageLoaded(`${key}-local-waterfall`)}
                            onError={() => markShapImageLoaded(`${key}-local-waterfall`)}
                          />
                          <img
                            src={`data:image/png;base64,${localData.bar}`}
                            alt=""
                            className={styles.shapImageHidden}
                            onLoad={() => markShapImageLoaded(`${key}-local-bar`)}
                            onError={() => markShapImageLoaded(`${key}-local-bar`)}
                          />
                        </>
                      )}
                      {globalData && !globalData.error && (
                        <>
                          <img
                            src={globalData.summary_plot}
                            alt=""
                            className={styles.shapImageHidden}
                            onLoad={() => markShapImageLoaded(`${key}-global-summary`)}
                            onError={() => markShapImageLoaded(`${key}-global-summary`)}
                          />
                          <img
                            src={globalData.importance_bar}
                            alt=""
                            className={styles.shapImageHidden}
                            onLoad={() => markShapImageLoaded(`${key}-global-importance`)}
                            onError={() => markShapImageLoaded(`${key}-global-importance`)}
                          />
                        </>
                      )}
                    </React.Fragment>
                  );
                })}
              </div>
            </div>
          ) : (
            <details
              className={styles.shapDetails}
              open={isShapExpanded}
              onToggle={(e) => setIsShapExpanded((e.target as HTMLDetailsElement).open)}
            >
              <summary className={styles.shapSummary}>
                <span className={styles.shapTitle}>SHAP Explanations</span>
                <span className={styles.shapSummaryHint}>Click to expand</span>
              </summary>

              <div className={styles.shapBody}>
                {/* Local SHAP */}
                {prediction.local_explanations && (
                  <>
                    <h4 className={styles.shapSectionTitle}>Local SHAP: This Prediction</h4>
                    {['malaria', 'ad', 'typhoid'].map((key) => {
                      const diseaseName = key === 'ad' ? 'Acute Diarrhea' : key.charAt(0).toUpperCase() + key.slice(1);
                      const data = prediction.local_explanations[key];
                      if (!data) return null;

                      return (
                        <div key={`local-${key}`} className={styles.shapDiseaseSection}>
                          <h5 className={styles.shapDiseaseTitle}>{diseaseName}</h5>
                          <div className={styles.shapImagesGrid}>
                            <figure className={styles.shapFigure}>
                              <figcaption>Waterfall Plot</figcaption>
                              <img
                                src={`data:image/png;base64,${data.waterfall}`}
                                alt={`${diseaseName} Waterfall`}
                                className={styles.shapImage}
                                loading="lazy"
                              />
                            </figure>
                            <figure className={styles.shapFigure}>
                              <figcaption>Bar Plot</figcaption>
                              <img
                                src={`data:image/png;base64,${data.bar}`}
                                alt={`${diseaseName} Bar Plot`}
                                className={styles.shapImage}
                                loading="lazy"
                              />
                            </figure>
                          </div>
                        </div>
                      );
                    })}
                  </>
                )}

                {/* Global SHAP */}
                {prediction.global_explanations && (
                  <>
                    <h4 className={styles.shapSectionTitle}>Global SHAP: Model-wide Insights</h4>
                    {['malaria', 'ad', 'typhoid'].map((key) => {
                      const diseaseName = key === 'ad' ? 'Acute Diarrhea' : key.charAt(0).toUpperCase() + key.slice(1);
                      const data = prediction.global_explanations[key];
                      if (!data || data.error) return null;

                      return (
                        <div key={`global-${key}`} className={styles.shapDiseaseSection}>
                          <h5 className={styles.shapDiseaseTitle}>{diseaseName}</h5>
                          <div className={styles.shapImagesGrid}>
                            <figure className={styles.shapFigure}>
                              <figcaption>Global Summary Plot</figcaption>
                              <img
                                src={data.summary_plot}
                                alt={`${diseaseName} Global Summary`}
                                className={styles.shapImage}
                                loading="lazy"
                              />
                            </figure>
                            <figure className={styles.shapFigure}>
                              <figcaption>Global Feature Importance</figcaption>
                              <img
                                src={data.importance_bar}
                                alt={`${diseaseName} Global Importance`}
                                className={styles.shapImage}
                                loading="lazy"
                              />
                            </figure>
                          </div>
                        </div>
                      );
                    })}
                  </>
                )}
              </div>
            </details>
          )}
        </Card>
      </div>
    </div>
  );
}