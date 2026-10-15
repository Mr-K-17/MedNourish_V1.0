import React, { useState, useEffect } from 'react';
import {
  Bot,
  ArrowLeft,
  ArrowRight,
  RotateCcw,
  Volume2,
  VolumeX,
  Check,
  AlertTriangle,
  Info,
  Save,
  CheckCircle2,
  XCircle,
  Activity,
} from 'lucide-react';
import { getDeficiencyClinicalInsight } from '../services/clinicalInsights';
import styles from './MedBotView.module.css';

interface QuestionOption {
  id: string;
  label: string;
  tag?: string;
  is_none_or_no: boolean;
}

interface QuestionnaireQuestion {
  id: string;
  step_number: number;
  body_region: string;
  question_text: string;
  explanation?: string;
  is_optional: boolean;
  is_lifestyle: boolean;
  allow_multiple: boolean;
  options: QuestionOption[];
}

interface QuestionnaireConfig {
  mode: 'simple' | 'standard';
  total_steps: number;
  disclaimer: string;
  questions: QuestionnaireQuestion[];
  package_version: string;
  matcher_version: string;
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

interface SymptomChip {
  tag: string;
  source_phrase: string;
  confidence: number;
}

interface EvaluateResponse {
  status: 'MATCHES_FOUND' | 'INSUFFICIENT_INFORMATION';
  message: string;
  disclaimer: string;
  collected_symptom_tags: string[];
  lifestyle_responses: Record<string, string[]>;
  nutrient_scores?: NutrientScore[];
  matched_entries: MatchedEntry[];
  unmatched_user_tags: string[];
  package_version: string;
  matcher_version: string;
  review_status: string;
}

interface MedBotViewProps {
  idToken: string;
  onBackToDashboard: () => void;
}

export const MedBotView: React.FC<MedBotViewProps> = ({
  idToken,
  onBackToDashboard,
}) => {
  // Mode selection state: null = mode picker, 'simple' | 'standard'
  const [selectedMode, setSelectedMode] = useState<'simple' | 'standard' | null>(null);
  const [config, setConfig] = useState<QuestionnaireConfig | null>(null);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [answers, setAnswers] = useState<Record<string, { optionIds: string[]; skipped: boolean }>>({});
  const [isLoadingConfig, setIsLoadingConfig] = useState<boolean>(false);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [evaluationResult, setEvaluationResult] = useState<EvaluateResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  // Phase 2 (c) Free-text extraction state
  const [freeText, setFreeText] = useState<string>('');
  const [isExtracting, setIsExtracting] = useState<boolean>(false);
  const [extractedChips, setExtractedChips] = useState<SymptomChip[]>([]);
  const [extractMessage, setExtractMessage] = useState<string | null>(null);

  const handleExtractSymptoms = async () => {
    if (!freeText.trim()) return;
    setIsExtracting(true);
    setExtractMessage(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/medbot/extract', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({ text: freeText }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'SYMPTOMS_EXTRACTED') {
          setExtractedChips((prev) => {
            const existingTags = new Set(prev.map((c) => c.tag));
            const newChips = data.chips.filter((c: SymptomChip) => !existingTags.has(c.tag));
            return [...prev, ...newChips];
          });
          setExtractMessage(`Extracted ${data.chips.length} symptom tag(s). Review or remove below.`);
        } else {
          setExtractMessage(data.message || 'No recognized nutritional symptoms detected.');
        }
      } else {
        setExtractMessage('Failed to extract symptoms from text.');
      }
    } catch {
      setExtractMessage('Unable to reach symptom extraction service.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleRemoveChip = (chipTag: string) => {
    setExtractedChips((prev) => prev.filter((c) => c.tag !== chipTag));
  };

  // Load questions when mode is selected
  useEffect(() => {
    if (!selectedMode) return;
    loadQuestionnaire(selectedMode);
  }, [selectedMode]);

  // Clean up speech synthesis on unmount
  useEffect(() => {
    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const loadQuestionnaire = async (mode: 'simple' | 'standard') => {
    setIsLoadingConfig(true);
    setErrorMessage(null);
    setEvaluationResult(null);
    setCurrentStepIndex(0);
    setAnswers({});
    setSaveSuccess(false);

    try {
      const res = await fetch(`http://127.0.0.1:8000/v1/medbot/questions?mode=${mode}`, {
        headers: {
          Authorization: `Bearer ${idToken}`,
        },
      });
      if (res.ok) {
        const data: QuestionnaireConfig = await res.json();
        setConfig(data);
      } else {
        setErrorMessage('Failed to load MedBot questionnaire.');
      }
    } catch {
      setErrorMessage('Backend service unreachable. Check if API server is running.');
    } finally {
      setIsLoadingConfig(false);
    }
  };

  const handleSpeak = (text: string) => {
    if (!('speechSynthesis' in window)) {
      alert('Speech read-aloud is not supported on this browser.');
      return;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  const currentQuestion = config ? config.questions[currentStepIndex] : null;

  const handleOptionSelect = (optionId: string) => {
    if (!currentQuestion) return;
    const qId = currentQuestion.id;
    const currentAns = answers[qId] || { optionIds: [], skipped: false };

    if (currentQuestion.allow_multiple) {
      const exists = currentAns.optionIds.includes(optionId);
      const newOptionIds = exists
        ? currentAns.optionIds.filter((id) => id !== optionId)
        : [...currentAns.optionIds, optionId];
      setAnswers((prev) => ({
        ...prev,
        [qId]: { optionIds: newOptionIds, skipped: false },
      }));
    } else {
      // Single select (Simple mode yes/no or standard single choice)
      setAnswers((prev) => ({
        ...prev,
        [qId]: { optionIds: [optionId], skipped: false },
      }));
    }
  };

  const handleSkipQuestion = () => {
    if (!currentQuestion) return;
    setAnswers((prev) => ({
      ...prev,
      [currentQuestion.id]: { optionIds: [], skipped: true },
    }));
    handleNextStep();
  };

  const handleNextStep = () => {
    if (!config) return;
    if (currentStepIndex < config.questions.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    } else {
      // Last step reached -> submit for evaluation
      handleSubmitEvaluation();
    }
  };

  const handlePrevStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  const handleSubmitEvaluation = async () => {
    if (!config || !selectedMode) return;
    setIsEvaluating(true);
    setErrorMessage(null);

    const formattedAnswers = config.questions.map((q) => {
      const ans = answers[q.id];
      if (!ans || ans.skipped) {
        return { question_id: q.id, selected_option_ids: [], skipped: true };
      }
      return { question_id: q.id, selected_option_ids: ans.optionIds, skipped: false };
    });

    try {
      const res = await fetch('http://127.0.0.1:8000/v1/medbot/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({
          mode: selectedMode,
          answers: formattedAnswers,
          confirmed_free_text_tags: extractedChips.map((c) => c.tag),
        }),
      });

      if (res.ok) {
        const data: EvaluateResponse = await res.json();
        setEvaluationResult(data);

        // Auto-save assessment to Files & Reports (Phase 5 requirement)
        try {
          fetch('http://127.0.0.1:8000/v1/medbot/save', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${idToken}`,
            },
            body: JSON.stringify({
              session_type: 'MedBot',
              body_region_filter: null,
              selected_tags: data.collected_symptom_tags,
              matched_entries: data.matched_entries,
              package_version: data.package_version,
              matcher_version: data.matcher_version,
            }),
          }).then((r) => {
            if (r.ok) setSaveSuccess(true);
          });
        } catch {
          // Non-fatal auto-save
        }
      } else {
        setErrorMessage('Failed to evaluate questionnaire answers.');
      }
    } catch {
      setErrorMessage('Unable to connect to evaluation service.');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleSaveAssessment = async () => {
    if (!evaluationResult || !config) return;
    setIsSaving(true);
    setErrorMessage(null);

    try {
      const res = await fetch('http://127.0.0.1:8000/v1/medbot/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({
          session_type: 'MedBot',
          body_region_filter: null,
          selected_tags: evaluationResult.collected_symptom_tags,
          matched_entries: evaluationResult.matched_entries,
          package_version: evaluationResult.package_version,
          matcher_version: evaluationResult.matcher_version,
        }),
      });

      if (res.ok) {
        setSaveSuccess(true);
      } else {
        setErrorMessage('Failed to save assessment to history.');
      }
    } catch {
      setErrorMessage('Unable to connect to reports persistence service.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleResetSession = () => {
    setSelectedMode(null);
    setConfig(null);
    setCurrentStepIndex(0);
    setAnswers({});
    setEvaluationResult(null);
    setErrorMessage(null);
    setSaveSuccess(false);
  };

  // Render: 1. Mode Picker
  if (!selectedMode) {
    return (
      <div className={styles.container}>
        <div className={styles.headerBar}>
          <button
            type="button"
            onClick={onBackToDashboard}
            className={styles.backButton}
          >
            <ArrowLeft size={16} /> Back to Dashboard
          </button>
          <div className={styles.titleArea}>
            <Bot size={22} color="var(--color-primary)" />
            <span style={{ fontWeight: 600 }}>MedBot Guided Consultation</span>
          </div>
        </div>

        <div className={styles.modePickerCard}>
          <h2 className={styles.modePickerTitle}>Choose Your Questionnaire Mode</h2>
          <p className={styles.modePickerSubtitle}>
            MedBot guides you through anatomical symptom questions to match against educational reference tables.
            No diagnosis or clinical predictions are made.
          </p>

          <div className={styles.modeGrid}>
            <button
              type="button"
              className={styles.modeOption}
              onClick={() => setSelectedMode('simple')}
            >
              <span className={styles.modeOptionTitle}>
                <CheckCircle2 size={20} color="var(--color-primary)" /> Simple Mode
              </span>
              <p className={styles.modeOptionDesc}>
                Quick yes/no questions with large buttons and plain-language prompts for each body region.
              </p>
            </button>

            <button
              type="button"
              className={styles.modeOption}
              onClick={() => setSelectedMode('standard')}
            >
              <span className={styles.modeOptionTitle}>
                <Bot size={20} color="var(--color-primary)" /> Standard Mode
              </span>
              <p className={styles.modeOptionDesc}>
                Detailed multi-select symptom questions across specific anatomical changes, signs, and optional lifestyle context.
              </p>
            </button>
          </div>

          <div className={styles.disclaimerBanner}>
            <Info size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong>Educational Prototype Notice:</strong> Results are reference-table matches only and do not replace professional medical evaluation. If you have urgent or acute symptoms, use the Emergency Help option immediately.
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Render: 2. Results Screen
  if (evaluationResult) {
    return (
      <div className={styles.container}>
        <div className={styles.headerBar}>
          <button
            type="button"
            onClick={handleResetSession}
            className={styles.backButton}
          >
            <RotateCcw size={16} /> Start New Questionnaire
          </button>
          <div className={styles.titleArea}>
            <span className={styles.modeBadge}>{selectedMode} Mode</span>
            <button
              type="button"
              className={`${styles.listenButton} ${isSpeaking ? styles.listeningActive : ''}`}
              onClick={() =>
                handleSpeak(
                  `Reference match summary. ${evaluationResult.message}. Disclaimer: ${evaluationResult.disclaimer}`
                )
              }
            >
              {isSpeaking ? <VolumeX size={15} /> : <Volume2 size={15} />}
              {isSpeaking ? 'Stop' : 'Listen'}
            </button>
          </div>
        </div>

        <div className={styles.resultHeader}>
          <h2 className={styles.resultTitle}>MedBot Reference Match Summary</h2>
          <div className={styles.summaryMeta}>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
              Identified Symptoms:
            </span>
            {evaluationResult.collected_symptom_tags.length > 0 ? (
              evaluationResult.collected_symptom_tags.map((t) => (
                <span key={t} className={styles.tagChip}>
                  {t}
                </span>
              ))
            ) : (
              <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
                None reported
              </span>
            )}
          </div>

          <div className={styles.disclaimerBanner}>
            <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong>Educational Prototype Disclaimer:</strong> {evaluationResult.disclaimer}
            </div>
          </div>
        </div>

        {evaluationResult.status === 'INSUFFICIENT_INFORMATION' ? (
          <div className={styles.insufficientCard}>
            <Info size={36} color="var(--color-text-secondary)" />
            <h3 className={styles.insufficientTitle}>Insufficient Information</h3>
            <p className={styles.insufficientText}>
              {evaluationResult.message}
            </p>
            <button
              type="button"
              className={styles.secondaryBtn}
              onClick={handleResetSession}
            >
              <RotateCcw size={16} /> Retake Questionnaire
            </button>
          </div>
        ) : (
          <div className={styles.entriesList}>
            <h3 style={{ fontSize: '1.05rem', margin: '0 0 0.5rem 0', color: 'var(--color-text-primary)' }}>
              Nutrient Reference Match Patterns:
            </h3>

            {evaluationResult.nutrient_scores && evaluationResult.nutrient_scores.length > 0 ? (
              evaluationResult.nutrient_scores.map((nut) => (
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
                      Clinical Breakdown: Causes, Medical References & Pathophysiology (Why this happened)
                    </summary>
                    {(() => {
                      const insight = getDeficiencyClinicalInsight(nut.nutrient);
                      return (
                        <div className={styles.whyContent} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                          {/* 1. Reasoning Chain */}
                          <div style={{ background: '#f0fdf4', padding: '0.75rem', borderRadius: '6px', border: '1px solid #bbf7d0' }}>
                            <strong style={{ fontSize: '0.82rem', color: '#166534', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
                              <Activity size={14} /> Biological Reasoning & Pathophysiology:
                            </strong>
                            <p style={{ margin: 0, fontSize: '0.8rem', color: '#14532d', lineHeight: 1.5 }}>
                              {insight.reasoning}
                            </p>
                          </div>

                          {/* 2. Major Causes */}
                          <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                            <strong style={{ fontSize: '0.82rem', color: '#334155', display: 'block', marginBottom: '4px' }}>
                              Etiology & Major Causes (Risk Factors):
                            </strong>
                            <ul style={{ margin: 0, paddingLeft: '1.15rem', fontSize: '0.78rem', color: '#475569', lineHeight: 1.5 }}>
                              {insight.majorCauses.map((cause, cIdx) => (
                                <li key={cIdx}>{cause}</li>
                              ))}
                            </ul>
                          </div>

                          {/* 3. Clinical Medications & Supplementation */}
                          <div style={{ background: '#fffbeb', padding: '0.75rem', borderRadius: '6px', border: '1px solid #fde68a' }}>
                            <strong style={{ fontSize: '0.82rem', color: '#92400e', display: 'block', marginBottom: '4px' }}>
                              Clinical Medication & Pharmacological Reference:
                            </strong>
                            <ul style={{ margin: 0, paddingLeft: '1.15rem', fontSize: '0.78rem', color: '#78350f', lineHeight: 1.5 }}>
                              {insight.medications.map((med, mIdx) => (
                                <li key={mIdx}>{med}</li>
                              ))}
                            </ul>
                            <p style={{ margin: '6px 0 0 0', fontSize: '0.72rem', color: '#b45309', fontStyle: 'italic' }}>
                              * Reference only: Pharmacological dosing and therapeutic regimens require formal laboratory confirmation and a physician's prescription.
                            </p>
                          </div>

                          {/* 4. Matched Symptoms & Diagnostic Evidence */}
                          <div className={styles.entryTags}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
                              Reported Symptoms Matched:
                            </span>
                            {nut.matched_tags.map((t) => (
                              <span key={t} className={styles.matchedTagBadge}>
                                ✓ {t}
                              </span>
                            ))}
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
              evaluationResult.matched_entries.map((entry) => {
                const insight = getDeficiencyClinicalInsight(entry.vitamin_deficiency_association);
                return (
                  <div key={entry.class_label} className={styles.entryCard}>
                    <div className={styles.entryHeader}>
                      <h4 className={styles.entryTitle}>{entry.class_label.replace(/_/g, ' ')}</h4>
                      <span className={styles.matchBadge}>
                        {entry.match_count} of {entry.total_condition_tags} tags matched
                      </span>
                    </div>
                    <div className={styles.deficiencyAssociation}>
                      <strong>Associated Deficiency:</strong> {entry.vitamin_deficiency_association} ({entry.body_region})
                    </div>
                    <div className={styles.entryTags}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                        Matched tags:
                      </span>
                      {entry.matched_tags.map((t) => (
                        <span key={t} className={styles.matchedTagBadge}>
                          ✓ {t}
                        </span>
                      ))}
                    </div>

                    <details style={{ marginTop: '0.75rem', fontSize: '0.8rem' }}>
                      <summary style={{ cursor: 'pointer', color: 'var(--color-primary)', fontWeight: 600 }}>
                        Clinical Causes, Medications & Reasoning
                      </summary>
                      <div style={{ padding: '0.6rem', background: '#f8fafc', borderRadius: '6px', marginTop: '0.4rem', lineHeight: 1.5 }}>
                        <p style={{ margin: '0 0 4px 0' }}><strong>Pathology:</strong> {insight.reasoning}</p>
                        <p style={{ margin: '0 0 4px 0' }}><strong>Medications:</strong> {insight.medications.join('; ')}</p>
                        <p style={{ margin: 0 }}><strong>Causes:</strong> {insight.majorCauses.join('; ')}</p>
                      </div>
                    </details>
                  </div>
                );
              })
            )}
          </div>
        )}

        <div className={styles.actionRow}>
          <button
            type="button"
            className={styles.secondaryBtn}
            onClick={onBackToDashboard}
          >
            Return to Dashboard
          </button>

          {evaluationResult.status === 'MATCHES_FOUND' && (
            <button
              type="button"
              className={styles.primaryBtn}
              onClick={handleSaveAssessment}
              disabled={isSaving || saveSuccess}
            >
              {saveSuccess ? (
                <>
                  <Check size={16} /> Saved to Files & Reports
                </>
              ) : isSaving ? (
                'Saving Summary...'
              ) : (
                <>
                  <Save size={16} /> Save Summary to History
                </>
              )}
            </button>
          )}
        </div>
      </div>
    );
  }

  // Render: 3. Active Step in Questionnaire
  if (isLoadingConfig || !config || !currentQuestion) {
    return (
      <div className={styles.container}>
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--color-text-secondary)' }}>
          Loading MedBot questionnaire...
        </div>
      </div>
    );
  }

  const currentAnswer = answers[currentQuestion.id] || { optionIds: [], skipped: false };
  const progressPct = Math.round(((currentStepIndex + 1) / config.total_steps) * 100);

  return (
    <div className={styles.container}>
      <div className={styles.headerBar}>
        <button
          type="button"
          onClick={handleResetSession}
          className={styles.backButton}
        >
          <XCircle size={16} /> Cancel Session
        </button>

        <div className={styles.titleArea}>
          <span className={styles.modeBadge}>{selectedMode} Mode</span>
          <button
            type="button"
            className={`${styles.listenButton} ${isSpeaking ? styles.listeningActive : ''}`}
            onClick={() => handleSpeak(currentQuestion.question_text)}
          >
            {isSpeaking ? <VolumeX size={15} /> : <Volume2 size={15} />}
            {isSpeaking ? 'Stop' : 'Listen'}
          </button>
        </div>
      </div>

      <div className={styles.questionCard}>
        <div>
          <div className={styles.progressRow}>
            <span>
              Question {currentStepIndex + 1} of {config.total_steps}
            </span>
            <span>{progressPct}% completed</span>
          </div>
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: `${progressPct}%` }} />
          </div>
        </div>

        <div>
          <span className={styles.regionTag}>{currentQuestion.body_region}</span>
          <h2 className={styles.questionTitle}>{currentQuestion.question_text}</h2>
        </div>

        {currentQuestion.explanation && (
          <p className={styles.questionExplanation}>{currentQuestion.explanation}</p>
        )}

        {currentQuestion.is_lifestyle && (
          <p className={styles.lifestyleNotice}>
            <strong>Optional Context:</strong> This lifestyle question provides background context only. Your answer will never change any symptom match results.
          </p>
        )}

        <div className={styles.optionsList}>
          {currentQuestion.options.map((opt) => {
            const isSelected = currentAnswer.optionIds.includes(opt.id);
            return (
              <button
                key={opt.id}
                type="button"
                className={`${styles.optionButton} ${isSelected ? styles.optionSelected : ''}`}
                onClick={() => handleOptionSelect(opt.id)}
              >
                <div className={styles.checkboxIndicator}>
                  {isSelected && <Check size={14} />}
                </div>
                <span>{opt.label}</span>
              </button>
            );
          })}
        </div>

        {selectedMode === 'standard' && (
          <div className={styles.freeTextContainer}>
            <label htmlFor="medbot-free-text" className={styles.freeTextLabel}>
              Describe how you feel (Optional)
            </label>
            <p className={styles.freeTextSubtext}>
              Type your symptoms in everyday language (e.g. &quot;tired, cracked corners of mouth, but no fever&quot;).
              Confirmed tags are combined with your choices; raw text is never stored.
            </p>
            <textarea
              id="medbot-free-text"
              className={styles.freeTextArea}
              placeholder="e.g. I feel exhausted and have brittle nails and dry skin..."
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
            />
            <div className={styles.freeTextActions}>
              <button
                type="button"
                className={styles.extractButton}
                disabled={isExtracting || !freeText.trim()}
                onClick={handleExtractSymptoms}
              >
                {isExtracting ? 'Extracting...' : 'Extract Symptoms'}
              </button>
            </div>
            {extractMessage && (
              <div style={{ fontSize: '0.75rem', color: '#0369a1' }}>{extractMessage}</div>
            )}
            {extractedChips.length > 0 && (
              <div className={styles.extractedChipsSection}>
                <span className={styles.chipsLabel}>Confirmed Extracted Symptoms:</span>
                <div className={styles.chipsList}>
                  {extractedChips.map((chip) => (
                    <span key={chip.tag} className={styles.chipItem}>
                      <span>{chip.tag}</span>
                      <button
                        type="button"
                        className={styles.chipRemoveBtn}
                        onClick={() => handleRemoveChip(chip.tag)}
                        title={`Remove tag (matched from "${chip.source_phrase}")`}
                      >
                        &times;
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <div className={styles.navBar}>
          <button
            type="button"
            className={styles.secondaryBtn}
            onClick={handlePrevStep}
            disabled={currentStepIndex === 0}
          >
            <ArrowLeft size={16} /> Back
          </button>

          <div className={styles.navGroup}>
            <button
              type="button"
              className={styles.secondaryBtn}
              onClick={handleSkipQuestion}
            >
              Skip Step
            </button>

            <button
              type="button"
              className={styles.primaryBtn}
              onClick={handleNextStep}
              disabled={isEvaluating}
            >
              {currentStepIndex === config.total_steps - 1 ? (
                isEvaluating ? (
                  'Evaluating...'
                ) : (
                  'Review Matches'
                )
              ) : (
                <>
                  Continue <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {errorMessage && (
        <div style={{ color: '#b91c1c', background: '#fee2e2', padding: '0.75rem', borderRadius: '6px' }}>
          {errorMessage}
        </div>
      )}
    </div>
  );
};
