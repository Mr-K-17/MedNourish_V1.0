import React, { useState, useEffect } from 'react';
import {
  Search,
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  BookOpen,
  RefreshCw,
  Info,
  Bookmark,
  Check,
  Activity,
} from 'lucide-react';
import { getDeficiencyClinicalInsight } from '../services/clinicalInsights';
import styles from './SymptomExplorer.module.css';

interface TagItem {
  tag: string;
  label: string;
}

interface CategoriesData {
  regions: string[];
  tags_by_region: Record<string, TagItem[]>;
  total_tags: number;
  package_version: string;
}

interface MatchedEntry {
  class_label: string;
  body_region: string;
  category: string;
  vitamin_deficiency_association: string;
  matched_tags: string[];
  match_count: number;
  total_condition_tags: number;
  review_status: string;
}

interface ContributingRow {
  class_label: string;
  body_region: string;
  category?: string;
  vitamin_deficiency?: string;
  row_match_percentage: number;
  matched_tags: string[];
  match_count: number;
  total_condition_tags: number;
}

interface NutrientScore {
  nutrient: string;
  percentage: number;
  percentage_kind: string;
  percentage_explanation: string;
  risk_band: 'High' | 'Moderate' | 'Low' | string;
  risk_band_label: string;
  matched_tags: string[];
  contributing_rows: ContributingRow[];
  kind: string;
}

interface MatchResponse {
  status: 'MATCHES_FOUND' | 'INSUFFICIENT_INFORMATION';
  message: string;
  disclaimer: string;
  nutrient_scores?: NutrientScore[];
  matched_entries: MatchedEntry[];
  unmatched_user_tags: string[];
  package_version: string;
  matcher_version: string;
}

interface SymptomExplorerProps {
  idToken: string;
  onBackToDashboard: () => void;
}

export const SymptomExplorer: React.FC<SymptomExplorerProps> = ({
  idToken,
  onBackToDashboard,
}) => {
  const [categories, setCategories] = useState<CategoriesData | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<string>('ALL');
  const [searchFilter, setSearchFilter] = useState<string>('');
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [isLoadingCategories, setIsLoadingCategories] = useState<boolean>(true);
  const [isMatching, setIsMatching] = useState<boolean>(false);
  const [matchResult, setMatchResult] = useState<MatchResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  useEffect(() => {
    fetchCategories();
  }, [idToken]);

  const fetchCategories = async () => {
    setIsLoadingCategories(true);
    setErrorMessage(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/explorer/categories', {
        headers: {
          Authorization: `Bearer ${idToken}`,
        },
      });
      if (res.ok) {
        const data: CategoriesData = await res.json();
        setCategories(data);
      } else {
        setErrorMessage('Failed to load symptom categories from server.');
      }
    } catch {
      setErrorMessage('Backend service unreachable. Check if API server is running.');
    } finally {
      setIsLoadingCategories(false);
    }
  };

  const handleToggleTag = (tag: string) => {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) {
        next.delete(tag);
      } else {
        next.add(tag);
      }
      return next;
    });
  };

  const handleClearSelection = () => {
    setSelectedTags(new Set());
    setMatchResult(null);
  };

  const handleExecuteMatch = async () => {
    setIsMatching(true);
    setErrorMessage(null);
    try {
      const payload = {
        selected_tags: Array.from(selectedTags),
        body_region_filter: selectedRegion === 'ALL' ? null : selectedRegion,
      };
      const res = await fetch('http://127.0.0.1:8000/v1/explorer/match', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data: MatchResponse = await res.json();
        setMatchResult(data);
        setSaveSuccess(false);
      } else {
        setErrorMessage('Error executing reference match query.');
      }
    } catch {
      setErrorMessage('Unable to connect to reference matcher service.');
    } finally {
      setIsMatching(false);
    }
  };

  const handleSaveSummary = async () => {
    if (!matchResult || matchResult.matched_entries.length === 0) {
      return;
    }
    setIsSaving(true);
    setErrorMessage(null);
    try {
      const payload = {
        session_type: 'Explorer',
        body_region_filter: selectedRegion === 'ALL' ? null : selectedRegion,
        selected_tags: Array.from(selectedTags),
        matched_entries: matchResult.matched_entries,
        package_version: matchResult.package_version,
        matcher_version: matchResult.matcher_version,
      };

      const res = await fetch('http://127.0.0.1:8000/v1/reports/summaries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setSaveSuccess(true);
      } else {
        setErrorMessage('Failed to save summary to reports.');
      }
    } catch {
      setErrorMessage('Unable to connect to reports service.');
    } finally {
      setIsSaving(false);
    }
  };

  // Compute available tags for active region and search filter
  const displayedTags: { region: string; tags: TagItem[] }[] = [];
  if (categories) {
    const targetRegions =
      selectedRegion === 'ALL' ? categories.regions : [selectedRegion];

    for (const reg of targetRegions) {
      const allTagsInRegion = categories.tags_by_region[reg] || [];
      const filtered = allTagsInRegion.filter((t) =>
        t.label.toLowerCase().includes(searchFilter.toLowerCase()) ||
        t.tag.toLowerCase().includes(searchFilter.toLowerCase())
      );
      if (filtered.length > 0) {
        displayedTags.push({ region: reg, tags: filtered });
      }
    }
  }

  return (
    <div className={styles.explorerContainer}>
      {/* Top Header / Navigation */}
      <div className={styles.headerBar}>
        <button
          type="button"
          onClick={onBackToDashboard}
          className={styles.backButton}
          aria-label="Return to Dashboard"
        >
          <ArrowLeft size={18} /> Back to Dashboard
        </button>

        <div className={styles.versionBadge}>
          <BookOpen size={14} /> Curated Reference {categories?.package_version || 'v1.0'}
        </div>
      </div>

      <div className={styles.titleSection}>
        <h2 className={styles.title}>Symptom Reference Explorer</h2>
        <p className={styles.subtitle}>
          Browse and select nutritional symptom tags to review documented associations in medical reference literature.
          This tool is for educational reference only and does not diagnose conditions.
        </p>
      </div>

      {errorMessage && (
        <div className={styles.errorAlert} role="alert">
          <AlertCircle size={18} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Two-Column Layout */}
      <div className={styles.layoutGrid}>
        {/* Left Column: Tag Browser & Selector */}
        <section className={styles.browserCard} aria-labelledby="browse-tags-heading">
          <div className={styles.cardHeader}>
            <h3 id="browse-tags-heading" className={styles.cardTitle}>
              1. Browse & Select Symptom Tags
            </h3>
            {selectedTags.size > 0 && (
              <button
                type="button"
                onClick={handleClearSelection}
                className={styles.clearBtn}
              >
                Clear all ({selectedTags.size})
              </button>
            )}
          </div>

          {/* Region Tabs */}
          <div className={styles.regionTabs} role="tablist" aria-label="Body Regions">
            <button
              type="button"
              role="tab"
              aria-selected={selectedRegion === 'ALL'}
              className={`${styles.regionTab} ${selectedRegion === 'ALL' ? styles.regionTabActive : ''}`}
              onClick={() => setSelectedRegion('ALL')}
            >
              All Regions
            </button>
            {categories?.regions.map((reg) => (
              <button
                key={reg}
                type="button"
                role="tab"
                aria-selected={selectedRegion === reg}
                className={`${styles.regionTab} ${selectedRegion === reg ? styles.regionTabActive : ''}`}
                onClick={() => setSelectedRegion(reg)}
              >
                {reg}
              </button>
            ))}
          </div>

          {/* Search Filter Input */}
          <div className={styles.searchWrapper}>
            <Search size={16} className={styles.searchIcon} aria-hidden="true" />
            <input
              type="text"
              placeholder="Search symptom tags (e.g., nightblindness, dryskin)..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className={styles.searchInput}
              aria-label="Filter symptom tags"
            />
          </div>

          {/* Tag List Container */}
          {isLoadingCategories ? (
            <div className={styles.loadingBox}>
              <RefreshCw size={20} className={styles.spinner} />
              <span>Loading reference symptom tags...</span>
            </div>
          ) : (
            <div className={styles.tagGroupsContainer}>
              {displayedTags.length === 0 ? (
                <p className={styles.noTagsFound}>No symptom tags match "{searchFilter}".</p>
              ) : (
                displayedTags.map((group) => (
                  <div key={group.region} className={styles.regionGroup}>
                    <h4 className={styles.regionGroupTitle}>{group.region}</h4>
                    <div className={styles.tagChips}>
                      {group.tags.map((t) => {
                        const isSelected = selectedTags.has(t.tag);
                        return (
                          <button
                            key={t.tag}
                            type="button"
                            onClick={() => handleToggleTag(t.tag)}
                            className={`${styles.tagChip} ${isSelected ? styles.tagChipSelected : ''}`}
                            aria-pressed={isSelected}
                          >
                            {isSelected && <CheckCircle2 size={14} className={styles.chipCheck} />}
                            {t.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Match Query Action */}
          <div className={styles.matchActionBar}>
            <span className={styles.selectionCounter}>
              <strong>{selectedTags.size}</strong> tag(s) selected
            </span>
            <button
              type="button"
              disabled={isMatching}
              onClick={handleExecuteMatch}
              className={styles.matchButton}
            >
              {isMatching ? (
                <>
                  <RefreshCw size={16} className={styles.spinner} /> Searching...
                </>
              ) : (
                <>
                  <Search size={16} /> Look Up Reference Matches
                </>
              )}
            </button>
          </div>
        </section>

        {/* Right Column: Reference Match Summary & Educational Guidance */}
        <section className={styles.resultsCard} aria-labelledby="results-heading">
          <div className={styles.cardHeader}>
            <h3 id="results-heading" className={styles.cardTitle}>
              2. Reference Match Summary
            </h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {matchResult && (
                <span className={styles.resultBadge}>
                  {matchResult.status === 'MATCHES_FOUND'
                    ? `${matchResult.matched_entries.length} Association(s)`
                    : 'Notice'}
                </span>
              )}
              {matchResult && matchResult.status === 'MATCHES_FOUND' && (
                <button
                  type="button"
                  onClick={handleSaveSummary}
                  disabled={isSaving || saveSuccess}
                  className={styles.saveSummaryBtn}
                  title="Save summary to your personal Files & Reports timeline"
                >
                  {saveSuccess ? (
                    <>
                      <Check size={14} /> Saved to Reports
                    </>
                  ) : isSaving ? (
                    <>
                      <RefreshCw size={14} className={styles.spinner} /> Saving...
                    </>
                  ) : (
                    <>
                      <Bookmark size={14} /> Save Summary
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {!matchResult ? (
            <div className={styles.emptyState}>
              <Info size={32} className={styles.emptyIcon} aria-hidden="true" />
              <h4>No Query Executed Yet</h4>
              <p>
                Select one or more symptom tags from the panel on the left and click
                <strong> "Look Up Reference Matches"</strong> to view documented nutritional associations.
              </p>
            </div>
          ) : matchResult.status === 'INSUFFICIENT_INFORMATION' ? (
            <div className={styles.insufficientState}>
              <AlertCircle size={28} className={styles.insufficientIcon} aria-hidden="true" />
              <h4>Insufficient Information</h4>
              <p className={styles.insufficientMsg}>{matchResult.message}</p>
              <p className={styles.insufficientGuidance}>
                Nutritional deficiencies require clinical assessment and diagnostic blood tests.
                If you are experiencing persistent or worsening health symptoms, please consult a qualified clinician.
              </p>
            </div>
          ) : (
            <div className={styles.matchedResultsList}>
              <div className={styles.resultsBanner}>
                <p>{matchResult.message}</p>
              </div>

              {matchResult.nutrient_scores && matchResult.nutrient_scores.length > 0 ? (
                matchResult.nutrient_scores.map((nut) => (
                  <div key={nut.nutrient} className={styles.nutrientScoreCard}>
                    <div className={styles.nutrientScoreHeader}>
                      <h4 className={styles.nutrientName}>{nut.nutrient}</h4>
                      <span
                        className={`${styles.riskBandBadge} ${
                          nut.risk_band === 'High'
                            ? styles.riskBandHigh
                            : nut.risk_band === 'Moderate'
                            ? styles.riskBandModerate
                            : styles.riskBandLow
                        }`}
                        title={nut.risk_band_label}
                      >
                        {nut.risk_band} Risk
                      </span>
                    </div>

                    <div className={styles.percentBarWrapper}>
                      <div className={styles.percentBarMeta}>
                        <span className={styles.percentKind}>{nut.percentage_kind}</span>
                        <span className={styles.percentValue}>{nut.percentage}%</span>
                      </div>
                      <div className={styles.percentBarTrack}>
                        <div
                          className={styles.percentBarFill}
                          style={{ width: `${Math.min(100, Math.max(0, nut.percentage))}%` }}
                        />
                      </div>
                      <p className={styles.percentExplanation}>{nut.percentage_explanation}</p>
                    </div>

                    <details className={styles.whyDetails}>
                      <summary className={styles.whySummary}>
                        Clinical Breakdown: Causes, Medical References & Pathophysiology
                      </summary>
                      {(() => {
                        const insight = getDeficiencyClinicalInsight(nut.nutrient);
                        return (
                          <div className={styles.whyContent} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {/* Reasoning */}
                            <div style={{ background: '#f0fdf4', padding: '0.65rem 0.85rem', borderRadius: '6px', border: '1px solid #bbf7d0' }}>
                              <strong style={{ fontSize: '0.8rem', color: '#166534', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '3px' }}>
                                <Activity size={13} /> Pathophysiological Reasoning:
                              </strong>
                              <p style={{ margin: 0, fontSize: '0.78rem', color: '#14532d', lineHeight: 1.5 }}>
                                {insight.reasoning}
                              </p>
                            </div>

                            {/* Causes */}
                            <div style={{ background: '#f8fafc', padding: '0.65rem 0.85rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                              <strong style={{ fontSize: '0.8rem', color: '#334155', display: 'block', marginBottom: '3px' }}>
                                Major Causes & Risk Factors:
                              </strong>
                              <ul style={{ margin: 0, paddingLeft: '1.15rem', fontSize: '0.76rem', color: '#475569', lineHeight: 1.5 }}>
                                {insight.majorCauses.map((c, idx) => (
                                  <li key={idx}>{c}</li>
                                ))}
                              </ul>
                            </div>

                            {/* Medications */}
                            <div style={{ background: '#fffbeb', padding: '0.65rem 0.85rem', borderRadius: '6px', border: '1px solid #fde68a' }}>
                              <strong style={{ fontSize: '0.8rem', color: '#92400e', display: 'block', marginBottom: '3px' }}>
                                Clinical Medication & Supplement Reference:
                              </strong>
                              <ul style={{ margin: 0, paddingLeft: '1.15rem', fontSize: '0.76rem', color: '#78350f', lineHeight: 1.5 }}>
                                {insight.medications.map((m, idx) => (
                                  <li key={idx}>{m}</li>
                                ))}
                              </ul>
                              <span style={{ fontSize: '0.7rem', color: '#b45309', display: 'block', marginTop: '4px', fontStyle: 'italic' }}>
                                * Clinical reference only — consult a physician for diagnostic confirmation and personalized dosing.
                              </span>
                            </div>

                            <div className={styles.tagsRow}>
                              <span className={styles.fieldLabel}>Matched Tags:</span>
                              <div className={styles.matchedTagPills}>
                                {nut.matched_tags.map((t) => (
                                  <span key={t} className={styles.matchedPill}>
                                    {t}
                                  </span>
                                ))}
                              </div>
                            </div>
                            <div className={styles.contributingRowsList}>
                              {nut.contributing_rows.map((row) => (
                                <div key={row.class_label} className={styles.contributingRowItem}>
                                  <span>{row.class_label.replace(/_/g, ' ')} ({row.body_region})</span>
                                  <strong>{row.row_match_percentage}% ({row.match_count}/{row.total_condition_tags} tags)</strong>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })()}
                    </details>
                  </div>
                ))
              ) : (
                matchResult.matched_entries.map((item, idx) => {
                  const insight = getDeficiencyClinicalInsight(item.vitamin_deficiency_association);
                  return (
                    <div key={`${item.class_label}-${idx}`} className={styles.matchItem}>
                      <div className={styles.matchItemHeader}>
                        <div className={styles.matchTitleBlock}>
                          <span className={styles.matchRegionBadge}>{item.body_region}</span>
                          <h4 className={styles.matchClassName}>{item.class_label.replace(/_/g, ' ')}</h4>
                        </div>
                        <span className={styles.matchCountPill}>
                          <strong>{item.match_count}</strong> of {item.total_condition_tags} tags matched
                        </span>
                      </div>

                      <div className={styles.matchBody}>
                        <div className={styles.deficiencyRow}>
                          <span className={styles.fieldLabel}>Nutrient Reference:</span>
                          <span className={styles.fieldValue}>{item.vitamin_deficiency_association}</span>
                        </div>

                        <div className={styles.tagsRow}>
                          <span className={styles.fieldLabel}>Matched Tags:</span>
                          <div className={styles.matchedTagPills}>
                            {item.matched_tags.map((t) => (
                              <span key={t} className={styles.matchedPill}>
                                {t}
                              </span>
                            ))}
                          </div>
                        </div>

                        <details style={{ marginTop: '0.6rem', fontSize: '0.8rem' }}>
                          <summary style={{ cursor: 'pointer', color: 'var(--color-primary)', fontWeight: 600 }}>
                            Clinical Causes, Medications & Reasoning
                          </summary>
                          <div style={{ padding: '0.5rem', background: '#f8fafc', borderRadius: '6px', marginTop: '0.35rem', lineHeight: 1.5 }}>
                            <p style={{ margin: '0 0 3px 0' }}><strong>Pathology:</strong> {insight.reasoning}</p>
                            <p style={{ margin: '0 0 3px 0' }}><strong>Medications:</strong> {insight.medications.join('; ')}</p>
                            <p style={{ margin: 0 }}><strong>Causes:</strong> {insight.majorCauses.join('; ')}</p>
                          </div>
                        </details>
                      </div>

                      <div className={styles.matchItemFooter}>
                        <span className={styles.reviewStatusLabel}>
                          Review Status: <em>{item.review_status}</em>
                        </span>
                      </div>
                    </div>
                  );
                })
              )}

              {matchResult.unmatched_user_tags.length > 0 && (
                <div className={styles.unmatchedBox}>
                  <h5>Unmatched Query Tags:</h5>
                  <div className={styles.unmatchedChips}>
                    {matchResult.unmatched_user_tags.map((t) => (
                      <span key={t} className={styles.unmatchedChip}>
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Educational Disclaimer Footer */}
          <div className={styles.disclaimerBox} role="note">
            <p className={styles.disclaimerText}>
              <strong>Educational Prototype Notice:</strong>{' '}
              {matchResult?.disclaimer ||
                'MEDNOURISH is an educational prototype. Results are reference-table matches and general health education, never medical diagnoses, predictions, or risk assessments. Discuss any symptom concerns with a qualified clinician.'}
            </p>
          </div>
        </section>
      </div>
    </div>
  );
};
