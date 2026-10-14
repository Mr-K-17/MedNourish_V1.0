import React, { useState, useEffect } from 'react';
import {
  FileText,
  ArrowLeft,
  Trash2,
  Calendar,
  RefreshCw,
  BookOpen,
  Info,
  Printer,
  BarChart2,
  ShieldAlert,
  Layers,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import styles from './ReportsView.module.css';

interface MatchedEntry {
  class_label: string;
  body_region: string;
  category: string;
  vitamin_deficiency_association: string;
  matched_tags: string[];
  match_count: number;
  total_condition_tags: number;
  row_match_percentage?: number;
  review_status: string;
}

interface SavedSummaryItem {
  id: string;
  session_type: string;
  body_region_filter?: string;
  selected_tags: string[];
  match_count_total: number;
  top_deficiency_associations: string[];
  package_version: string;
  matcher_version: string;
  review_status: string;
  created_at: string;
}

interface SavedSummaryDetail extends SavedSummaryItem {
  matched_entries: MatchedEntry[];
  disclaimer: string;
}

interface AggregatedNutrient {
  nutrient: string;
  reference_pct: number;
  xgboost_pct: number;
  lightgbm_pct: number;
  image_pct: number;
  final_pct: number;
  demo_risk_band: string;
}

interface ChartDataPayload {
  grouped_bar: any[];
  ranked_horizontal: any[];
  radar: any[];
  donut_risk: any[];
  timeline: any[];
  heatmap: any[];
}

interface FinalReportCard {
  probable_deficiencies: string;
  demo_risk_band: string;
  supporting_sources: string[];
  suggested_measures: string[];
  disclaimer: string;
  emergency_link: string;
}

interface ReportsAggregateResponse {
  entries_count: number;
  recency_weights: number[];
  aggregated_nutrients: AggregatedNutrient[];
  chart_data: ChartDataPayload;
  final_report_card: FinalReportCard;
  formula_note: string;
}

interface ReportsViewProps {
  idToken: string;
  onBackToDashboard: () => void;
  onOpenEmergencyModal?: () => void;
}

const DONUT_COLORS: Record<string, string> = {
  'High Risk Band': '#ef4444',
  'Moderate Risk Band': '#f59e0b',
  'Low Risk Band': '#10b981',
};

const LINE_COLORS = ['#0f766e', '#3b82f6', '#8b5cf6', '#ec4899'];

export const ReportsView: React.FC<ReportsViewProps> = ({
  idToken,
  onBackToDashboard,
  onOpenEmergencyModal,
}) => {
  const [activeTab, setActiveTab] = useState<'analytics' | 'history'>('analytics');
  const [summaries, setSummaries] = useState<SavedSummaryItem[]>([]);
  const [selectedSummary, setSelectedSummary] = useState<SavedSummaryDetail | null>(null);
  const [aggregateData, setAggregateData] = useState<ReportsAggregateResponse | null>(null);
  const [isLoadingList, setIsLoadingList] = useState<boolean>(true);
  const [isLoadingAggregate, setIsLoadingAggregate] = useState<boolean>(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchSummaries();
    fetchAggregate();
  }, [idToken]);

  const fetchAggregate = async () => {
    setIsLoadingAggregate(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/reports/aggregate', {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        const data: ReportsAggregateResponse = await res.json();
        setAggregateData(data);
      }
    } catch {
      // Non-fatal fallback
    } finally {
      setIsLoadingAggregate(false);
    }
  };

  const fetchSummaries = async () => {
    setIsLoadingList(true);
    setErrorMessage(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/reports/summaries', {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSummaries(data.summaries || []);
        if (data.summaries.length > 0) {
          fetchSummaryDetail(data.summaries[0].id);
        }
      } else {
        setErrorMessage('Failed to load saved summaries.');
      }
    } catch {
      setErrorMessage('Network error connecting to reports service.');
    } finally {
      setIsLoadingList(false);
    }
  };

  const fetchSummaryDetail = async (id: string) => {
    setIsLoadingDetail(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/v1/reports/summaries/${id}`, {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        const data: SavedSummaryDetail = await res.json();
        setSelectedSummary(data);
      }
    } catch {
      // Non-fatal
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleDeleteSummary = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Delete this saved summary permanently?')) return;
    setIsDeleting(id);
    try {
      const res = await fetch(`http://127.0.0.1:8000/v1/reports/summaries/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        setSuccessMessage('Summary deleted successfully.');
        setSummaries((prev) => prev.filter((s) => s.id !== id));
        if (selectedSummary?.id === id) {
          setSelectedSummary(null);
        }
        fetchAggregate();
      }
    } catch {
      setErrorMessage('Failed to delete summary.');
    } finally {
      setIsDeleting(null);
    }
  };

  const getRiskColor = (band: string) => {
    if (band.toLowerCase().includes('high')) return '#ef4444';
    if (band.toLowerCase().includes('moderate')) return '#f59e0b';
    return '#10b981';
  };

  return (
    <div className={styles.container}>
      {/* Header Bar */}
      <div className={styles.headerBar}>
        <button
          type="button"
          onClick={onBackToDashboard}
          className={styles.backButton}
        >
          <ArrowLeft size={16} /> Back to Dashboard
        </button>

        <div className={styles.titleArea}>
          <FileText size={22} color="var(--color-primary)" />
          <h2 className={styles.title}>Files & Assessment Reports</h2>
        </div>

        <div className={styles.tabToggleGroup}>
          <button
            type="button"
            className={`${styles.tabToggleBtn} ${activeTab === 'analytics' ? styles.tabToggleActive : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            <BarChart2 size={15} /> Multi-Engine Analytics
          </button>
          <button
            type="button"
            className={`${styles.tabToggleBtn} ${activeTab === 'history' ? styles.tabToggleActive : ''}`}
            onClick={() => setActiveTab('history')}
          >
            <Layers size={15} /> Check-in Snapshots ({summaries.length})
          </button>
          <button
            type="button"
            className={styles.printBtn}
            onClick={() => window.print()}
            title="Print entire assessment report"
          >
            <Printer size={15} /> Print Report
          </button>
        </div>
      </div>

      {/* Educational Prototype Notice */}
      <div className={styles.prototypeNotice}>
        <Info size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
        <span>
          <strong>Educational Prototype Notice:</strong> Results are algorithmic reference-table matches and multi-engine estimates, never medical diagnoses, probability of disease, or clinical prescriptions. Discuss symptom patterns with a qualified clinician.
        </span>
      </div>

      {successMessage && <div className={styles.successAlert}>{successMessage}</div>}
      {errorMessage && <div className={styles.errorAlert}>{errorMessage}</div>}

      {/* ================= TAB 1: MULTI-ENGINE ANALYTICS & CHARTS ================= */}
      {activeTab === 'analytics' && (
        <div className={styles.analyticsView}>
          {isLoadingAggregate ? (
            <div className={styles.loadingBox}>
              <RefreshCw size={22} className={styles.spinner} />
              <span>Computing multi-engine recency aggregation...</span>
            </div>
          ) : !aggregateData || aggregateData.entries_count === 0 ? (
            <div className={styles.emptyCard}>
              <Info size={36} color="#0f766e" />
              <h3>No Saved Assessment Data Available</h3>
              <p>Complete a symptom evaluation in MedBot, Symptom Explorer, or MedScan to generate multi-engine analytics and longitudinal charts.</p>
            </div>
          ) : (
            <>
              {/* FINAL REPORT CARD */}
              <div className={styles.finalReportCard}>
                <div className={styles.reportCardHeader}>
                  <div>
                    <span className={styles.reportCardEyebrow}>Composite Assessment</span>
                    <h3 className={styles.reportCardTitle}>Multi-Engine Screening Summary</h3>
                  </div>
                  <span
                    className={styles.riskBandBadge}
                    style={{ backgroundColor: getRiskColor(aggregateData.final_report_card.demo_risk_band) }}
                  >
                    Demo Risk Band: {aggregateData.final_report_card.demo_risk_band}
                  </span>
                </div>

                <div className={styles.probableDefSummary}>
                  <strong>{aggregateData.final_report_card.probable_deficiencies}</strong>
                </div>

                <div className={styles.reportCardGrid}>
                  {/* Supporting Sources */}
                  <div className={styles.reportCardSection}>
                    <h5 className={styles.sectionHeading}>Supporting Evidence Sources</h5>
                    <ul className={styles.sourcesList}>
                      {aggregateData.final_report_card.supporting_sources.map((s, idx) => (
                        <li key={idx}>&bull; {s}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Suggested Measures */}
                  <div className={styles.reportCardSection}>
                    <h5 className={styles.sectionHeading}>Suggested Next Measures</h5>
                    <ul className={styles.measuresList}>
                      {aggregateData.final_report_card.suggested_measures.map((m, idx) => (
                        <li key={idx}>&bull; {m}</li>
                      ))}
                    </ul>
                    {onOpenEmergencyModal && (
                      <button
                        type="button"
                        onClick={onOpenEmergencyModal}
                        className={styles.emergencyLinkBtn}
                      >
                        <ShieldAlert size={14} /> Urgent Care & Crisis Help
                      </button>
                    )}
                  </div>
                </div>

                <div className={styles.reportCardFooter}>
                  <span>Recency Weighting Formula: Latest {aggregateData.entries_count} snapshots blended with decay weights [{aggregateData.recency_weights.join(', ')}].</span>
                  <span className={styles.academicNotice}>Never medication, supplements, or dosages.</span>
                </div>
              </div>

              {/* CHARTS GRID (6 RECHARTS COMPONENTS) */}
              <div className={styles.chartsGrid}>
                {/* 1. Grouped Bar Chart: Nutrient x Engine Source */}
                <div className={styles.chartCard}>
                  <div className={styles.chartHeader}>
                    <h4>Nutrient Likelihood by Engine Source</h4>
                    <span className={styles.chartTag}>Grouped Bar</span>
                  </div>
                  <div className={styles.chartContainer}>
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={aggregateData.chart_data.grouped_bar} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                        <XAxis dataKey="nutrient" angle={-25} textAnchor="end" interval={0} height={50} tick={{ fontSize: 11 }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                        <Bar dataKey="reference_pct" name="Reference %" fill="#0f766e" />
                        <Bar dataKey="xgboost_pct" name="XGBoost %" fill="#3b82f6" />
                        <Bar dataKey="lightgbm_pct" name="LightGBM %" fill="#8b5cf6" />
                        <Bar dataKey="image_pct" name="Image %" fill="#ec4899" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <p className={styles.chartCaption}>
                    Percentage contributions across literature reference table matches, XGBoost/LightGBM tabular estimators (unverified synthetic data), and anatomical computer vision models.
                  </p>
                </div>

                {/* 2. Ranked Horizontal Bar: Final Nutrient % */}
                <div className={styles.chartCard}>
                  <div className={styles.chartHeader}>
                    <h4>Ranked Composite Nutrient Likelihood</h4>
                    <span className={styles.chartTag}>Horizontal Bar</span>
                  </div>
                  <div className={styles.chartContainer}>
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart layout="vertical" data={aggregateData.chart_data.ranked_horizontal} margin={{ top: 10, right: 20, left: 20, bottom: 0 }}>
                        <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <YAxis type="category" dataKey="nutrient" width={110} tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Bar dataKey="final_pct" name="Composite Likelihood %">
                          {aggregateData.chart_data.ranked_horizontal.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={getRiskColor(entry.demo_risk_band)} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <p className={styles.chartCaption}>
                    Final blended likelihood % calculated with recency-weighted decay (&ge;60% High risk band, 30-59% Moderate, &lt;30% Low).
                  </p>
                </div>

                {/* 3. Radar Chart: Multi-Axial Nutrient Pattern */}
                <div className={styles.chartCard}>
                  <div className={styles.chartHeader}>
                    <h4>Multi-Axial Nutrient Radar Profile</h4>
                    <span className={styles.chartTag}>Radar</span>
                  </div>
                  <div className={styles.chartContainer}>
                    <ResponsiveContainer width="100%" height={260}>
                      <RadarChart outerRadius={85} data={aggregateData.chart_data.radar}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="nutrient" tick={{ fontSize: 10 }} />
                        <PolarRadiusAxis domain={[0, 100]} angle={30} tick={{ fontSize: 9 }} />
                        <Radar name="Composite Pattern" dataKey="final_pct" stroke="#0f766e" fill="#0f766e" fillOpacity={0.45} />
                        <Tooltip />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                  <p className={styles.chartCaption}>
                    Multi-axial radial view showing the balance and co-occurrence of observable nutritional physical signs.
                  </p>
                </div>

                {/* 4. Donut Chart: Risk Bands Distribution */}
                <div className={styles.chartCard}>
                  <div className={styles.chartHeader}>
                    <h4>Risk Band Distribution</h4>
                    <span className={styles.chartTag}>Donut</span>
                  </div>
                  <div className={styles.chartContainer}>
                    <ResponsiveContainer width="100%" height={260}>
                      <PieChart>
                        <Pie
                          data={aggregateData.chart_data.donut_risk}
                          dataKey="count"
                          nameKey="band"
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={80}
                          paddingAngle={5}
                          label={({ name, value }) => (value > 0 ? `${name}: ${value}` : '')}
                        >
                          {aggregateData.chart_data.donut_risk.map((entry, index) => (
                            <Cell key={`donut-${index}`} fill={DONUT_COLORS[entry.band] || '#94a3b8'} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <p className={styles.chartCaption}>
                    Proportion of tracked nutrient markers falling into Heuristic Demo Risk categories.
                  </p>
                </div>

                {/* 5. Line Chart: Top-Nutrient % Over Time */}
                <div className={styles.chartCard}>
                  <div className={styles.chartHeader}>
                    <h4>Longitudinal Nutrient Tracking</h4>
                    <span className={styles.chartTag}>Timeline Line</span>
                  </div>
                  <div className={styles.chartContainer}>
                    <ResponsiveContainer width="100%" height={260}>
                      <LineChart data={aggregateData.chart_data.timeline} margin={{ top: 10, right: 20, left: -20, bottom: 20 }}>
                        <XAxis dataKey="date" angle={-20} textAnchor="end" tick={{ fontSize: 10 }} height={40} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                        {Object.keys(aggregateData.chart_data.timeline[0] || {})
                          .filter((k) => k !== 'date')
                          .map((nutName, idx) => (
                            <Line
                              key={nutName}
                              type="monotone"
                              dataKey={nutName}
                              stroke={LINE_COLORS[idx % LINE_COLORS.length]}
                              strokeWidth={2}
                              dot={{ r: 3 }}
                            />
                          ))}
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  <p className={styles.chartCaption}>
                    Tracking of leading nutrient likelihood percentages across sequential user assessment check-ins.
                  </p>
                </div>

                {/* 6. Heatmap: Body-Region x Nutrient */}
                <div className={styles.chartCard}>
                  <div className={styles.chartHeader}>
                    <h4>Anatomical Region vs. Nutrient Heatmap</h4>
                    <span className={styles.chartTag}>Matrix Heatmap</span>
                  </div>
                  <div className={styles.heatmapWrapper}>
                    <table className={styles.heatmapTable}>
                      <thead>
                        <tr>
                          <th>Region</th>
                          {Array.from(new Set(aggregateData.chart_data.heatmap.map((h: any) => h.nutrient))).map((nut) => (
                            <th key={nut}>{nut}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {Array.from(new Set(aggregateData.chart_data.heatmap.map((h: any) => h.body_region))).map((reg) => (
                          <tr key={reg}>
                            <td className={styles.regionHeaderCell}>{reg}</td>
                            {Array.from(new Set(aggregateData.chart_data.heatmap.map((h: any) => h.nutrient))).map((nut) => {
                              const cell = aggregateData.chart_data.heatmap.find((h: any) => h.body_region === reg && h.nutrient === nut);
                              const val = cell ? cell.value : 0;
                              const alpha = Math.min(1, val / 100);
                              return (
                                <td
                                  key={`${reg}-${nut}`}
                                  className={styles.heatmapCell}
                                  style={{ backgroundColor: `rgba(15, 118, 110, ${alpha})`, color: alpha > 0.45 ? '#ffffff' : '#1e293b' }}
                                >
                                  {val > 0 ? `${val}%` : '—'}
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className={styles.chartCaption}>
                    Anatomical matrix cross-referencing observable physical regions against correlated nutritional markers.
                  </p>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* ================= TAB 2: CHECK-IN SNAPSHOTS & DETAIL ================= */}
      {activeTab === 'history' && (
        <div className={styles.mainGrid}>
          {/* Left: Saved List */}
          <section className={styles.listSection} aria-label="Saved Summaries History">
            <div className={styles.sectionHeader}>
              <h3 className={styles.sectionTitle}>Saved Check-ins</h3>
              <span className={styles.badge}>{summaries.length} saved</span>
            </div>

            {isLoadingList ? (
              <div className={styles.loadingBox}>
                <RefreshCw size={20} className={styles.spinner} />
                <span>Loading your saved summaries...</span>
              </div>
            ) : summaries.length === 0 ? (
              <div className={styles.emptyState}>
                <Calendar size={32} />
                <p>No check-in summaries saved yet.</p>
                <small>Run a check in MedBot, Symptom Explorer, or MedScan to auto-save records.</small>
              </div>
            ) : (
              <div className={styles.summaryList}>
                {summaries.map((item) => {
                  const isSelected = selectedSummary?.id === item.id;
                  const formattedDate = new Date(item.created_at).toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  });

                  return (
                    <div
                      key={item.id}
                      className={`${styles.summaryItem} ${isSelected ? styles.selectedItem : ''}`}
                      onClick={() => fetchSummaryDetail(item.id)}
                      role="button"
                      tabIndex={0}
                    >
                      <div className={styles.itemHeader}>
                        <span className={styles.itemDate}>{formattedDate}</span>
                        <button
                          type="button"
                          onClick={(e) => handleDeleteSummary(item.id, e)}
                          disabled={isDeleting === item.id}
                          className={styles.deleteBtn}
                          title="Delete this saved record"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>

                      <div className={styles.itemMeta}>
                        <span className={styles.sourceTag}>{item.session_type}</span>
                        {item.body_region_filter && <span className={styles.regionTag}>{item.body_region_filter}</span>}
                        <span className={styles.matchCountPill}>{item.match_count_total} Association(s)</span>
                      </div>

                      <div className={styles.tagsPreview}>
                        <strong>Tags:</strong> {item.selected_tags.slice(0, 3).join(', ')}
                        {item.selected_tags.length > 3 && ` +${item.selected_tags.length - 3}`}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          {/* Right: Selected Detail */}
          <section className={styles.detailCard}>
            <div className={styles.cardHeader}>
              <h3 className={styles.cardTitle}>Snapshot Detail</h3>
              {selectedSummary && (
                <span className={styles.versionTag}>
                  <BookOpen size={12} /> {selectedSummary.package_version}
                </span>
              )}
            </div>

            {isLoadingDetail ? (
              <div className={styles.loadingBox}>
                <RefreshCw size={20} className={styles.spinner} />
                <span>Loading record details...</span>
              </div>
            ) : !selectedSummary ? (
              <div className={styles.emptyDetailState}>
                <Info size={32} />
                <h4>Select a Check-in</h4>
                <p>Click on any check-in from the list to view its recorded details.</p>
              </div>
            ) : (
              <div className={styles.detailContent}>
                <div className={styles.detailMetaBanner}>
                  <div>
                    <h4 className={styles.detailTitle}>{selectedSummary.session_type} Assessment Snapshot</h4>
                    <span className={styles.detailTimestamp}>
                      Recorded on {new Date(selectedSummary.created_at).toLocaleString()}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => handleDeleteSummary(selectedSummary.id, e)}
                    disabled={isDeleting === selectedSummary.id}
                    className={styles.deleteDetailBtn}
                  >
                    <Trash2 size={15} /> Delete Record
                  </button>
                </div>

                <div className={styles.detailSection}>
                  <h5 className={styles.detailSectionTitle}>Selected Symptom Tags</h5>
                  <div className={styles.detailTagChips}>
                    {selectedSummary.selected_tags.map((t) => (
                      <span key={t} className={styles.detailTagChip}>
                        {t}
                      </span>
                    ))}
                  </div>
                </div>

                <div className={styles.detailSection}>
                  <h5 className={styles.detailSectionTitle}>
                    Matched Reference Classes ({selectedSummary.matched_entries.length})
                  </h5>
                  <div className={styles.entriesList}>
                    {selectedSummary.matched_entries.map((entry, idx) => (
                      <div key={`${entry.class_label}-${idx}`} className={styles.entryCard}>
                        <div className={styles.entryHeader}>
                          <div className={styles.entryTitleGroup}>
                            <span className={styles.entryRegion}>{entry.body_region}</span>
                            <span className={styles.entryLabel}>{entry.class_label.replace(/_/g, ' ')}</span>
                          </div>
                          <span className={styles.entryMatchPill}>
                            {entry.row_match_percentage !== undefined && (
                              <strong>{entry.row_match_percentage}% (Reference match %) &bull; </strong>
                            )}
                            {entry.match_count} of {entry.total_condition_tags} tags matched
                          </span>
                        </div>
                        <div className={styles.entryNutrient}>
                          <strong>Associated Reference:</strong> {entry.vitamin_deficiency_association}
                        </div>
                        <div className={styles.entryMatchedTags}>
                          <strong>Matched Tags:</strong> {entry.matched_tags.join(', ')}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className={styles.disclaimerBox}>
                  <p className={styles.disclaimerText}>
                    <strong>Educational Notice:</strong> {selectedSummary.disclaimer}
                  </p>
                </div>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
};
