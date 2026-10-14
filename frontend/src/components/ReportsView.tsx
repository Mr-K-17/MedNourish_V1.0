import React, { useState, useEffect } from 'react';
import {
  FileText,
  ArrowLeft,
  Trash2,
  Calendar,
  AlertCircle,
  RefreshCw,
  BookOpen,
  ChevronRight,
  Info,
  Printer,
} from 'lucide-react';
import styles from './ReportsView.module.css';

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

interface ReportsViewProps {
  idToken: string;
  onBackToDashboard: () => void;
}

export const ReportsView: React.FC<ReportsViewProps> = ({
  idToken,
  onBackToDashboard,
}) => {
  const [summaries, setSummaries] = useState<SavedSummaryItem[]>([]);
  const [selectedSummary, setSelectedSummary] = useState<SavedSummaryDetail | null>(null);
  const [isLoadingList, setIsLoadingList] = useState<boolean>(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchSummaries();
  }, [idToken]);

  const fetchSummaries = async () => {
    setIsLoadingList(true);
    setErrorMessage(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/reports/summaries', {
        headers: {
          Authorization: `Bearer ${idToken}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setSummaries(data.summaries || []);
      } else {
        setErrorMessage('Failed to load saved reports from server.');
      }
    } catch {
      setErrorMessage('Backend service unreachable. Check if API is running.');
    } finally {
      setIsLoadingList(false);
    }
  };

  const handleSelectSummary = async (id: string) => {
    setIsLoadingDetail(true);
    setErrorMessage(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/v1/reports/summaries/${id}`, {
        headers: {
          Authorization: `Bearer ${idToken}`,
        },
      });
      if (res.ok) {
        const data: SavedSummaryDetail = await res.json();
        setSelectedSummary(data);
      } else {
        setErrorMessage('Failed to load summary details.');
      }
    } catch {
      setErrorMessage('Unable to load summary details.');
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleDeleteSummary = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this saved reference summary?')) {
      return;
    }
    setIsDeleting(id);
    setErrorMessage(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/v1/reports/summaries/${id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${idToken}`,
        },
      });
      if (res.ok) {
        setSummaries((prev) => prev.filter((s) => s.id !== id));
        if (selectedSummary?.id === id) {
          setSelectedSummary(null);
        }
        setSuccessMessage('Summary deleted successfully.');
        setTimeout(() => setSuccessMessage(null), 3500);
      } else {
        setErrorMessage('Failed to delete summary record.');
      }
    } catch {
      setErrorMessage('Error communicating with server during deletion.');
    } finally {
      setIsDeleting(null);
    }
  };

  return (
    <div className={styles.reportsContainer}>
      {/* Header Bar */}
      <div className={styles.headerBar}>
        <button
          type="button"
          onClick={onBackToDashboard}
          className={styles.backButton}
          aria-label="Return to Dashboard"
        >
          <ArrowLeft size={18} /> Back to Dashboard
        </button>

        <div className={styles.sectionBadge}>
          <FileText size={14} /> Files & Reports (Phase 1B)
        </div>
      </div>

      <div className={styles.titleSection}>
        <h2 className={styles.title}>Saved Summaries & Check-in History</h2>
        <p className={styles.subtitle}>
          Secure timeline of saved educational reference match sessions.
          Records contain selected symptom tags and matching reference tables. No clinical risk scores are stored.
        </p>
      </div>

      {errorMessage && (
        <div className={styles.errorAlert} role="alert">
          <AlertCircle size={18} />
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className={styles.successAlert} role="status">
          <span>{successMessage}</span>
        </div>
      )}

      {/* Main Grid: List on Left, Detail on Right */}
      <div className={styles.layoutGrid}>
        {/* Left: Summary History Timeline */}
        <section className={styles.listCard} aria-labelledby="history-list-heading">
          <div className={styles.cardHeader}>
            <h3 id="history-list-heading" className={styles.cardTitle}>
              Saved Check-ins ({summaries.length})
            </h3>
            <button
              type="button"
              onClick={fetchSummaries}
              className={styles.refreshBtn}
              aria-label="Refresh saved list"
            >
              <RefreshCw size={14} /> Refresh
            </button>
          </div>

          {isLoadingList ? (
            <div className={styles.loadingBox}>
              <RefreshCw size={20} className={styles.spinner} />
              <span>Loading saved check-ins...</span>
            </div>
          ) : summaries.length === 0 ? (
            <div className={styles.emptyState}>
              <Info size={32} className={styles.emptyIcon} />
              <h4>No Saved Summaries Yet</h4>
              <p>
                When you run the <strong>Symptom Reference Explorer</strong>, click
                <strong> "Save Summary to Reports"</strong> to keep a record of your matched tags and reference tables.
              </p>
            </div>
          ) : (
            <div className={styles.summaryList}>
              {summaries.map((item) => {
                const isSelected = selectedSummary?.id === item.id;
                const formattedDate = new Date(item.created_at).toLocaleString(undefined, {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                });

                return (
                  <div
                    key={item.id}
                    className={`${styles.summaryItem} ${isSelected ? styles.summaryItemSelected : ''}`}
                    onClick={() => handleSelectSummary(item.id)}
                    role="button"
                    tabIndex={0}
                    aria-pressed={isSelected}
                  >
                    <div className={styles.itemHeader}>
                      <span className={styles.dateBadge}>
                        <Calendar size={13} /> {formattedDate}
                      </span>
                      <button
                        type="button"
                        onClick={(e) => handleDeleteSummary(item.id, e)}
                        disabled={isDeleting === item.id}
                        className={styles.deleteBtn}
                        title="Delete this saved summary"
                        aria-label={`Delete saved summary from ${formattedDate}`}
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>

                    <div className={styles.itemBody}>
                      <div className={styles.itemMeta}>
                        <span className={styles.sourceTag}>{item.session_type}</span>
                        {item.body_region_filter && (
                          <span className={styles.regionTag}>{item.body_region_filter}</span>
                        )}
                        <span className={styles.matchCountPill}>
                          {item.match_count_total} Association(s)
                        </span>
                      </div>

                      <div className={styles.tagsPreview}>
                        <strong>Tags:</strong>{' '}
                        {item.selected_tags.slice(0, 4).join(', ')}
                        {item.selected_tags.length > 4 && ` +${item.selected_tags.length - 4} more`}
                      </div>

                      {item.top_deficiency_associations.length > 0 && (
                        <div className={styles.defPreview}>
                          <strong>Nutrients:</strong> {item.top_deficiency_associations.join(', ')}
                        </div>
                      )}
                    </div>

                    <div className={styles.itemFooter}>
                      <span className={styles.viewDetailHint}>
                        View Details <ChevronRight size={14} />
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* Right: Detailed View */}
        <section className={styles.detailCard} aria-labelledby="detail-heading">
          <div className={styles.cardHeader}>
            <h3 id="detail-heading" className={styles.cardTitle}>
              Summary Detail
            </h3>
            {selectedSummary && (
              <span className={styles.versionTag}>
                <BookOpen size={12} /> {selectedSummary.package_version}
              </span>
            )}
          </div>

          {isLoadingDetail ? (
            <div className={styles.loadingBox}>
              <RefreshCw size={20} className={styles.spinner} />
              <span>Loading summary details...</span>
            </div>
          ) : !selectedSummary ? (
            <div className={styles.emptyDetailState}>
              <Info size={32} className={styles.emptyIcon} />
              <h4>Select a Saved Summary</h4>
              <p>Click on any check-in from the list on the left to inspect the recorded reference matches.</p>
            </div>
          ) : (
            <div className={styles.detailContent}>
              <div className={styles.detailMetaBanner}>
                <div>
                  <h4 className={styles.detailTitle}>
                    {selectedSummary.session_type} Check-in Record
                  </h4>
                  <span className={styles.detailTimestamp}>
                    Saved on {new Date(selectedSummary.created_at).toLocaleString()}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <button
                    type="button"
                    onClick={() => window.print()}
                    className={styles.backButton}
                    style={{ padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}
                    title="Print this report summary or save as PDF"
                  >
                    <Printer size={15} /> Print Report
                  </button>
                  <button
                    type="button"
                    onClick={(e) => handleDeleteSummary(selectedSummary.id, e)}
                    disabled={isDeleting === selectedSummary.id}
                    className={styles.deleteDetailBtn}
                  >
                    <Trash2 size={16} /> Delete Record
                  </button>
                </div>
              </div>

              {/* Queried Tags */}
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

              {/* Matched Reference Classes */}
              <div className={styles.detailSection}>
                <h5 className={styles.detailSectionTitle}>
                  Matched Reference Table Classes ({selectedSummary.matched_entries.length})
                </h5>
                <div className={styles.entriesList}>
                  {selectedSummary.matched_entries.map((entry, idx) => (
                    <div key={`${entry.class_label}-${idx}`} className={styles.entryCard}>
                      <div className={styles.entryHeader}>
                        <div className={styles.entryTitleGroup}>
                          <span className={styles.entryRegion}>{entry.body_region}</span>
                          <span className={styles.entryLabel}>
                            {entry.class_label.replace(/_/g, ' ')}
                          </span>
                        </div>
                        <span className={styles.entryMatchPill}>
                          {entry.match_count} of {entry.total_condition_tags} tags matched
                        </span>
                      </div>

                      <div className={styles.entryNutrient}>
                        <strong>Associated Reference:</strong> {entry.vitamin_deficiency_association}
                      </div>

                      <div className={styles.entryMatchedTags}>
                        <strong>Matched:</strong> {entry.matched_tags.join(', ')}
                      </div>

                      <div className={styles.entryFooter}>
                        <span className={styles.reviewLabel}>
                          Status: <em>{entry.review_status}</em>
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Disclaimer */}
              <div className={styles.disclaimerBox} role="note">
                <p className={styles.disclaimerText}>
                  <strong>Educational Notice:</strong> {selectedSummary.disclaimer}
                </p>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
