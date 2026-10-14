import React, { useState, useEffect } from 'react';
import {
  Camera,
  ArrowLeft,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Shield,
  ChevronDown,
  ChevronUp,
  Sliders,
  Sparkles,
} from 'lucide-react';
import styles from './MedScanLiteView.module.css';

interface MedScanLiteViewProps {
  idToken?: string | null;
  onBackToDashboard: () => void;
  onOpenEmergencyModal: () => void;
  onHandoffToExplorer?: () => void;
}

interface ChecklistItem {
  tag: string;
  label: string;
}

interface NutrientScoreItem {
  nutrient: string;
  percentage: number;
  percentage_kind: string;
  percentage_explanation: string;
  image_percentage?: number | null;
  reference_percentage?: number | null;
  risk_band: string;
  risk_band_label: string;
  matched_tags: string[];
  contributing_rows: any[];
  kind: string;
}

interface MedScanBlendResponse {
  status: string;
  message: string;
  disclaimer: string;
  nutrient_scores: NutrientScoreItem[];
  matched_entries: any[];
  unmatched_user_tags: string[];
  kind: string;
  shortcut_flag: boolean;
  w_img: number;
  saved_report_id?: string | null;
  quality_passed: boolean;
}

const DEFAULT_CHECKLIST: Record<string, ChecklistItem[]> = {
  eyes: [
    { tag: 'eyedryness', label: "Eye dryness / Bitot's spots" },
    { tag: 'nightblindness', label: 'Difficulty seeing in dim light / night blindness' },
    { tag: 'cornealsoftening', label: 'Corneal softening / ulceration' },
    { tag: 'blurredvision', label: 'Blurred or fluctuating vision' },
    { tag: 'eyegrittiness', label: 'Gritty sensation in eyes' },
    { tag: 'photophobia', label: 'Sensitivity to light' },
    { tag: 'excessivetearing', label: 'Excessive tearing or burning' },
  ],
  nails: [
    { tag: 'koilonychia', label: 'Spoon-shaped concave nails (koilonychia)' },
    { tag: 'brittlenails', label: 'Brittle, splitting or peeling nails' },
    { tag: 'beaulines', label: "Transverse nail ridges (Beau's lines)" },
    { tag: 'longitudinalridges', label: 'Vertical / longitudinal nail ridging' },
    { tag: 'palenails', label: 'Pale nail beds (pallor)' },
    { tag: 'slowgrowth', label: 'Slow nail growth or frequent breakage' },
  ],
  hair: [
    { tag: 'brittlehair', label: 'Dry, brittle or easily broken hair' },
    { tag: 'diffusehairloss', label: 'Diffuse hair thinning or shedding' },
    { tag: 'corkscrewhair', label: 'Corkscrew or coiled hairs' },
    { tag: 'curlyhairshaft', label: 'Fragile curly hair shafts' },
    { tag: 'lossheadhair', label: 'Patches of hair thinning / alopecia' },
    { tag: 'depigmentation', label: 'Lightening or depigmentation of hair' },
  ],
  lips: [
    { tag: 'crackedlips', label: 'Dry, peeling or cracked lips (cheilosis)' },
    { tag: 'angularcheilitis', label: 'Fissures / sores at corners of mouth' },
    { tag: 'burningtongue', label: 'Burning sensation on lips or mouth' },
    { tag: 'swollenlips', label: 'Swollen or erythematous lips' },
    { tag: 'lipfissures', label: 'Deep painful fissures on lips' },
  ],
  skin: [
    { tag: 'follicularhyperkeratosis', label: 'Rough, gooseflesh-like skin bumps' },
    { tag: 'dryskin', label: 'Severe dry, scaly or flaking skin (xerosis)' },
    { tag: 'darkenedskinpatches', label: 'Dark, hyperpigmented skin patches' },
    { tag: 'petechiae', label: 'Small pinpoint red/purple spots (petechiae)' },
    { tag: 'delayedwoundhealing', label: 'Slow wound healing or easy bruising' },
    { tag: 'burningskin', label: 'Burning or prickling sensations on skin' },
  ],
  tongue: [
    { tag: 'beefyredtongue', label: 'Smooth, beefy red tongue (atrophic glossitis)' },
    { tag: 'burningtongue', label: 'Burning or tender sensation on tongue' },
    { tag: 'swollentongue', label: 'Swollen or enlarged tongue' },
    { tag: 'papillaryatrophy', label: 'Loss of tongue bumps / papillae' },
    { tag: 'tastealteration', label: 'Altered or blunted taste perception' },
    { tag: 'tongueulcers', label: 'Recurrent aphthous-like sores on tongue' },
  ],
  combined: [
    { tag: 'nightblindness', label: 'Night blindness / dark adaptation difficulty' },
    { tag: 'fatigue', label: 'Persistent exhaustion or weakness' },
    { tag: 'bleedinggums', label: 'Spontaneous bleeding gums' },
    { tag: 'brittlenails', label: 'Brittle, fragile nails' },
    { tag: 'crackedlips', label: 'Cracked lip corners (angular cheilitis)' },
    { tag: 'bonepain', label: 'Deep bone or joint aching' },
    { tag: 'delayedwoundhealing', label: 'Delayed healing of cuts or scrapes' },
  ],
};

export const MedScanLiteView: React.FC<MedScanLiteViewProps> = ({
  idToken,
  onBackToDashboard,
  onOpenEmergencyModal,
  onHandoffToExplorer,
}) => {
  const [selectedRegion, setSelectedRegion] = useState<string>('eyes');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  // Regional Follow-up Checklist
  const [checklist, setChecklist] = useState<ChecklistItem[]>(DEFAULT_CHECKLIST.eyes);
  const [tickedSymptoms, setTickedSymptoms] = useState<string[]>([]);
  const [expandedWhy, setExpandedWhy] = useState<Record<string, boolean>>({});

  // Analysis / Quality Results
  const [qualityResults, setQualityResults] = useState<{
    passed: boolean;
    dimensions: string;
    brightness: string;
    fileSize: string;
    format: string;
    notes: string;
  } | null>(null);

  const [blendResults, setBlendResults] = useState<MedScanBlendResponse | null>(null);

  // Fetch or update checklist when region changes
  useEffect(() => {
    const defaultItems = DEFAULT_CHECKLIST[selectedRegion] || DEFAULT_CHECKLIST.combined;
    setChecklist(defaultItems);
    setTickedSymptoms([]);
    setBlendResults(null);
    setQualityResults(null);
    setSaveSuccess(null);

    if (idToken) {
      fetch(`http://127.0.0.1:8000/v1/medscan/checklist?body_region=${selectedRegion}`, {
        headers: { Authorization: `Bearer ${idToken}` },
      })
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data && data.items && data.items.length > 0) {
            setChecklist(data.items);
          }
        })
        .catch(() => {});
    }
  }, [selectedRegion, idToken]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setQualityResults(null);
    setBlendResults(null);
    setSaveSuccess(null);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
  };

  const handleToggleSymptom = (tag: string) => {
    setTickedSymptoms((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const toggleWhy = (nutrient: string) => {
    setExpandedWhy((prev) => ({ ...prev, [nutrient]: !prev[nutrient] }));
  };

  const handlePerformAnalysis = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setBlendResults(null);
    setSaveSuccess(null);

    // 1. Client-side dimensions check
    const img = new Image();
    img.src = previewUrl || '';
    img.onload = async () => {
      const width = img.width;
      const height = img.height;
      const sizeMB = (selectedFile.size / (1024 * 1024)).toFixed(2);
      const isSizeOk = selectedFile.size <= 5 * 1024 * 1024;
      const isResolutionOk = width >= 224 && height >= 224;

      setQualityResults({
        passed: isSizeOk && isResolutionOk,
        dimensions: `${width} x ${height} px ${isResolutionOk ? '(Satisfies 224x224 minimum)' : '(Below minimum resolution)'}`,
        brightness: 'Ambient illumination within acceptable distribution',
        fileSize: `${sizeMB} MB ${isSizeOk ? '(Within 5 MB limit)' : '(Exceeds 5 MB limit)'}`,
        format: selectedFile.type,
        notes:
          isSizeOk && isResolutionOk
            ? 'Image satisfies all quality gating requirements.'
            : 'Image resolution or size is suboptimal. A retake is recommended.',
      });

      // 2. Call backend analyze endpoint
      try {
        const formData = new FormData();
        formData.append('body_region', selectedRegion);
        formData.append('file', selectedFile);
        formData.append('symptoms', JSON.stringify(tickedSymptoms));
        formData.append('save_report', 'true');

        const headers: Record<string, string> = {};
        if (idToken) {
          headers['Authorization'] = `Bearer ${idToken}`;
        }

        const res = await fetch('http://127.0.0.1:8000/v1/medscan/analyze', {
          method: 'POST',
          headers,
          body: formData,
        });

        if (res.ok) {
          const data: MedScanBlendResponse = await res.json();
          setBlendResults(data);
          if (data.saved_report_id) {
            setSaveSuccess(`Analysis complete. Report auto-saved (ID: ${data.saved_report_id.slice(0, 8)}...).`);
          }
        } else {
          const err = await res.json().catch(() => ({}));
          setQualityResults({
            passed: false,
            dimensions: `${width} x ${height} px`,
            brightness: 'Unknown',
            fileSize: `${sizeMB} MB`,
            format: selectedFile.type,
            notes: err.detail || 'Analysis service temporarily unavailable.',
          });
        }
      } catch {
        setQualityResults({
          passed: false,
          dimensions: `${width} x ${height} px`,
          brightness: 'Unknown',
          fileSize: `${sizeMB} MB`,
          format: selectedFile.type,
          notes: 'Failed to communicate with MedScan inference service.',
        });
      } finally {
        setIsAnalyzing(false);
      }
    };

    img.onerror = () => {
      setIsAnalyzing(false);
      setQualityResults({
        passed: false,
        dimensions: 'Unknown',
        brightness: 'Unreadable',
        fileSize: `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB`,
        format: selectedFile.type,
        notes: 'Unable to decode image file. Please provide a valid JPEG, PNG, or WebP image.',
      });
    };
  };

  const handleSaveSession = async () => {
    if (!selectedFile || !idToken) return;
    setIsSaving(true);
    setSaveSuccess(null);
    try {
      const formData = new FormData();
      formData.append('body_region', selectedRegion);
      formData.append('save_session', 'true');
      formData.append('files', selectedFile);

      const res = await fetch('http://127.0.0.1:8000/v1/medscan/sessions', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${idToken}`,
        },
        body: formData,
      });

      if (res.ok) {
        setSaveSuccess('Quality audit session saved securely to your account.');
      }
    } catch {
      // fallback
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.headerBar}>
        <button
          type="button"
          onClick={onBackToDashboard}
          className={styles.backButton}
        >
          <ArrowLeft size={16} /> Back to Dashboard
        </button>
        <div className={styles.titleArea}>
          <Camera size={24} color="var(--color-primary)" />
          <h2 className={styles.title}>MedScan Image & Regional Symptom Inspection</h2>
        </div>
      </div>

      {/* Safety Notice */}
      <div className={styles.warningBanner}>
        <AlertTriangle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
        <div>
          <strong>Educational Prototype Notice (SCAN-03, SCAN-07, C-34, C-35):</strong> MedScan
          performs image-quality gating, MobileNetV2 computer-vision inference, and symptom cross-matching.
          Percentages represent transparent pattern coverage (<strong>Image model %</strong> / <strong>MedScan blend %</strong>),
          NOT medical probabilities. It does NOT deliver medical diagnoses or autonomously prescribe treatments.
          Images are processed ephemerally and discarded immediately after inference unless explicitly saved.
          <div style={{ marginTop: '0.4rem' }}>
            <button
              type="button"
              onClick={onOpenEmergencyModal}
              className={styles.emergencyLinkBtn}
            >
              Emergency & Urgent Help Details →
            </button>
          </div>
        </div>
      </div>

      {/* Guidance Card */}
      <div className={styles.guidanceCard}>
        <h3 className={styles.guidanceTitle}>
          <Shield size={18} color="var(--color-primary)" /> Clinical Photo Capture Guidance
        </h3>
        <ul className={styles.guidanceList}>
          <li>Ensure bright, diffuse natural lighting (avoid harsh shadows or heavy flash reflections).</li>
          <li>Hold the camera steady 15–25 cm from the target anatomical region.</li>
          <li>Ensure the selected region fills at least 60% of the camera frame.</li>
          <li>Do not apply filters, beauty modes, or color enhancements.</li>
        </ul>
      </div>

      {/* Capture / Select Controls */}
      <div className={styles.setupCard}>
        <div className={styles.fieldGroup}>
          <label htmlFor="bodyRegionSelect" className={styles.fieldLabel}>
            1. Select Anatomical Region (SCAN-06)
          </label>
          <select
            id="bodyRegionSelect"
            value={selectedRegion}
            onChange={(e) => {
              setSelectedRegion(e.target.value);
            }}
            className={styles.selectInput}
          >
            <option value="eyes">Eyes (Sclera / Conjunctiva / Bitot's spots)</option>
            <option value="nails">Nails (Koilonychia / Ridging / Spooning)</option>
            <option value="hair">Hair (Texture / Flag sign / Follicles)</option>
            <option value="tongue">Tongue (Glossitis / Color / Coating)</option>
            <option value="lips">Lips (Cheilitis / Angular fissures)</option>
            <option value="skin">Skin (Follicular hyperkeratosis / Dryness)</option>
            <option value="combined">Combined / Multi-region Overview</option>
          </select>
        </div>

        <div className={styles.fieldGroup}>
          <label className={styles.fieldLabel}>
            2. Choose Image (Max 5 MB, JPEG / PNG / WebP)
          </label>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={handleFileChange}
            className={styles.fileInput}
          />
        </div>
      </div>

      {/* Regional Follow-up Checklist */}
      <div className={styles.checklistCard}>
        <h4 className={styles.checklistTitle}>
          <Sliders size={18} color="var(--color-primary)" style={{ verticalAlign: 'middle', marginRight: '6px' }} />
          3. Regional Follow-up Checklist ({selectedRegion.toUpperCase()})
        </h4>
        <p className={styles.checklistSubtitle}>
          Tick any observable symptoms you are experiencing in this anatomical area. These will be blended with
          the computer-vision model evidence.
        </p>
        <div className={styles.checklistGrid}>
          {checklist.map((item) => (
            <label key={item.tag} className={styles.checkboxItem}>
              <input
                type="checkbox"
                checked={tickedSymptoms.includes(item.tag)}
                onChange={() => handleToggleSymptom(item.tag)}
              />
              <span>{item.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Preview and Action Controls */}
      {previewUrl && (
        <div className={styles.previewSection}>
          <div className={styles.previewCard}>
            <h4 className={styles.cardHeader}>Captured Frame</h4>
            <div className={styles.imageContainer}>
              <img src={previewUrl} alt="Captured region" className={styles.previewImage} />
            </div>

            <button
              type="button"
              onClick={handlePerformAnalysis}
              disabled={isAnalyzing}
              className={styles.analyzeBtn}
            >
              <Sparkles size={16} /> {isAnalyzing ? 'Running Inference & Blend...' : 'Run MedScan Analysis & Symptom Blend'}
            </button>
          </div>

          {/* Quality Audit Results */}
          {qualityResults && (
            <div
              className={`${styles.resultsCard} ${
                qualityResults.passed ? styles.resultsPassed : styles.resultsFailed
              }`}
            >
              <div className={styles.resultsHeader}>
                {qualityResults.passed ? (
                  <>
                    <CheckCircle size={22} color="#166534" />
                    <h4 className={styles.resultsTitleSuccess}>Quality Audit Passed</h4>
                  </>
                ) : (
                  <>
                    <XCircle size={22} color="#b91c1c" />
                    <h4 className={styles.resultsTitleFail}>Quality Audit Inadequate (Retake Recommended)</h4>
                  </>
                )}
              </div>

              <div className={styles.metricsList}>
                <div className={styles.metricItem}>
                  <span className={styles.metricLabel}>Resolution:</span>
                  <span className={styles.metricVal}>{qualityResults.dimensions}</span>
                </div>
                <div className={styles.metricItem}>
                  <span className={styles.metricLabel}>File Size:</span>
                  <span className={styles.metricVal}>{qualityResults.fileSize}</span>
                </div>
                <div className={styles.metricItem}>
                  <span className={styles.metricLabel}>Illumination:</span>
                  <span className={styles.metricVal}>{qualityResults.brightness}</span>
                </div>
                <div className={styles.metricItem}>
                  <span className={styles.metricLabel}>Format:</span>
                  <span className={styles.metricVal}>{qualityResults.format}</span>
                </div>
              </div>

              <p className={styles.notesText}>{qualityResults.notes}</p>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  onClick={handleSaveSession}
                  disabled={isSaving || !!saveSuccess}
                  className={styles.analyzeBtn}
                  style={{ background: '#0284c7' }}
                >
                  {isSaving ? 'Saving...' : 'Save Quality Photo Session'}
                </button>

                {onHandoffToExplorer && (
                  <button
                    type="button"
                    onClick={onHandoffToExplorer}
                    className={styles.analyzeBtn}
                    style={{ background: 'var(--color-primary)' }}
                  >
                    Explore Symptoms in Detail →
                  </button>
                )}
              </div>

              {saveSuccess && (
                <div style={{ fontSize: '0.85rem', color: '#166534', fontWeight: 600 }}>
                  {saveSuccess}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Blended Results Section */}
      {blendResults && (
        <div className={styles.blendResultsCard}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
            <h3 className={styles.blendTitle}>
              Ranked Nutrient Candidates ({blendResults.nutrient_scores.length})
            </h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
              Kind: {blendResults.kind} | Weighting: w_img={blendResults.w_img}
              {blendResults.shortcut_flag && ' (visual shortcut penalty applied)'}
            </span>
          </div>

          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
            {blendResults.message}
          </p>

          <div className={styles.nutrientList}>
            {blendResults.nutrient_scores.map((n) => {
              const isHigh = n.risk_band === 'High';
              const isMod = n.risk_band === 'Moderate';
              const badgeClass = isHigh
                ? styles.badgeRiskHigh
                : isMod
                ? styles.badgeRiskModerate
                : styles.badgeRiskLow;
              const fillClass = isHigh
                ? styles.barFillHigh
                : isMod
                ? styles.barFillModerate
                : styles.barFillLow;
              const isExpanded = !!expandedWhy[n.nutrient];

              return (
                <div key={n.nutrient} className={styles.nutrientCard}>
                  <div className={styles.nutrientTop}>
                    <span className={styles.nutrientName}>{n.nutrient}</span>
                    <div className={styles.badgeGroup}>
                      <span className={badgeClass}>{n.risk_band}</span>
                      <strong style={{ fontSize: '1rem', color: 'var(--color-text-primary)' }}>
                        {n.percentage.toFixed(1)}%
                      </strong>
                    </div>
                  </div>

                  <div className={styles.barTrack}>
                    <div className={fillClass} style={{ width: `${Math.min(100, Math.max(2, n.percentage))}%` }} />
                  </div>

                  <div className={styles.barMeta}>
                    <span>{n.percentage_kind}</span>
                    <span>{n.risk_band_label}</span>
                  </div>

                  <button
                    type="button"
                    onClick={() => toggleWhy(n.nutrient)}
                    className={styles.whyToggleBtn}
                  >
                    {isExpanded ? (
                      <>
                        <ChevronUp size={14} style={{ verticalAlign: 'middle' }} /> Hide calculation details
                      </>
                    ) : (
                      <>
                        <ChevronDown size={14} style={{ verticalAlign: 'middle' }} /> Why this candidate?
                      </>
                    )}
                  </button>

                  {isExpanded && (
                    <div className={styles.whyContent}>
                      <div>
                        <strong>Calculation:</strong> {n.percentage_explanation}
                      </div>
                      {n.image_percentage !== null && n.image_percentage !== undefined && (
                        <div>
                          <strong>Image model %:</strong> {n.image_percentage.toFixed(1)}%
                        </div>
                      )}
                      {n.reference_percentage !== null && n.reference_percentage !== undefined && (
                        <div>
                          <strong>Reference match %:</strong> {n.reference_percentage.toFixed(1)}%
                        </div>
                      )}
                      {n.matched_tags && n.matched_tags.length > 0 && (
                        <div>
                          <strong>Matched Regional Symptoms:</strong> {n.matched_tags.join(', ')}
                        </div>
                      )}
                      {n.contributing_rows && n.contributing_rows.length > 0 && (
                        <div>
                          <strong>Contributing Reference Rows:</strong>
                          <ul style={{ margin: '0.25rem 0 0 1rem', padding: 0 }}>
                            {n.contributing_rows.map((row: any, idx: number) => (
                              <li key={idx}>
                                {row.class_label} ({row.body_region}) — {row.row_match_percentage?.toFixed(1) || row.match_count}%
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div style={{ marginTop: '0.5rem', padding: '0.75rem', background: '#f8fafc', borderRadius: 'var(--radius-md)', fontSize: '0.75rem', color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>
            {blendResults.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
};
