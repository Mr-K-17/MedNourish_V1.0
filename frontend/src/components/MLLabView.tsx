import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  AlertTriangle,
  Activity,
  Layers,
  Image as ImageIcon,
  FileCode,
  UploadCloud,
  BarChart3,
  Maximize2,
} from 'lucide-react';
import styles from './MLLabView.module.css';

interface MLLabViewProps {
  idToken: string;
  onBackToDashboard: () => void;
  onOpenEmergencyModal: () => void;
}

export const MLLabView: React.FC<MLLabViewProps> = ({
  idToken,
  onBackToDashboard,
  onOpenEmergencyModal,
}) => {
  const [activeTab, setActiveTab] = useState<'graphs' | 'tabular' | 'keywords' | 'image' | 'cards'>('graphs');
  const [selectedGraphModal, setSelectedGraphModal] = useState<{ title: string; src: string; desc: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Tab 1: Tabular Form State
  const [tabularForm, setTabularForm] = useState({
    gender: 'Female',
    smoking_status: 'Non-Smoker',
    alcohol_consumption: 'None',
    exercise_level: 'Moderate',
    diet_type: 'Omnivore',
    sun_exposure: 'Moderate',
    income_level: 'Middle',
    latitude_region: 'Temperate',
    age: 32,
    bmi: 22.4,
    hemoglobin_g_dl: 13.2,
    serum_vitamin_d_ng_ml: 28.5,
    serum_vitamin_b12_pg_ml: 410.0,
    serum_folate_ng_ml: 8.2,
    vitamin_a_percent_rda: 85.0,
    vitamin_c_percent_rda: 90.0,
    has_night_blindness: 0,
    has_fatigue: 0,
    has_bleeding_gums: 0,
    has_bone_pain: 0,
  });
  const [tabularResult, setTabularResult] = useState<any>(null);

  // Tab 2: Keyword Form State
  const [keywordRegion, setKeywordRegion] = useState('Eyes');
  const [keywordText, setKeywordText] = useState('dry cornea, night vision difficulty');
  const [keywordResult, setKeywordResult] = useState<any>(null);

  // Tab 3: Image Form State
  const [imageModel, setImageModel] = useState('combined');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imageResult, setImageResult] = useState<any>(null);

  // Tab 4: Model Cards State
  const [modelCards, setModelCards] = useState<any[]>([]);
  const [selectedCard, setSelectedCard] = useState<any>(null);

  useEffect(() => {
    if (activeTab === 'cards' && modelCards.length === 0) {
      loadModelCards();
    }
  }, [activeTab]);

  const loadModelCards = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/mllab/model-cards', {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setModelCards(data.cards || []);
        if (data.cards?.length > 0) {
          loadCardDetail(data.cards[0].card_id);
        }
      } else {
        const err = await res.json();
        setErrorMsg(err.detail || 'Failed to load model cards from ML Lab service.');
      }
    } catch {
      setErrorMsg('ML Lab service is currently unavailable. Start ml-service on port 8001.');
    } finally {
      setLoading(false);
    }
  };

  const loadCardDetail = async (cardId: string) => {
    setLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/v1/mllab/model-cards/${cardId}`, {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedCard(data);
      }
    } catch {
      // Ignored
    } finally {
      setLoading(false);
    }
  };

  const handleTabularSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setTabularResult(null);

    try {
      const res = await fetch('http://127.0.0.1:8000/v1/mllab/predict/tabular', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify(tabularForm),
      });

      if (res.ok) {
        const data = await res.json();
        setTabularResult(data);
      } else {
        const err = await res.json();
        setErrorMsg(err.detail || 'Prediction failed.');
      }
    } catch {
      setErrorMsg('ML Lab service is currently unavailable. Start ml-service on port 8001.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeywordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setKeywordResult(null);

    try {
      const res = await fetch('http://127.0.0.1:8000/v1/mllab/predict/keywords', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({
          body_region: keywordRegion,
          keywords: keywordText,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setKeywordResult(data);
      } else {
        const err = await res.json();
        setErrorMsg(err.detail || 'Keyword lookup failed.');
      }
    } catch {
      setErrorMsg('ML Lab service is currently unavailable. Start ml-service on port 8001.');
    } finally {
      setLoading(false);
    }
  };

  const handleImageSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMsg('Please select an image file to upload.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setImageResult(null);

    const formData = new FormData();
    formData.append('model_name', imageModel);
    formData.append('file', selectedFile);

    try {
      const res = await fetch('http://127.0.0.1:8000/v1/mllab/predict/image', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${idToken}`,
        },
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setImageResult(data);
      } else {
        const err = await res.json();
        setErrorMsg(err.detail || 'Image prediction failed.');
      }
    } catch {
      setErrorMsg('ML Lab service is currently unavailable. Start ml-service on port 8001.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      {/* 1. Mandatory Persistent Warning Banner */}
      <div className={styles.warningBanner}>
        <AlertTriangle size={24} style={{ flexShrink: 0, marginTop: '2px' }} />
        <div>
          <strong>Experimental ML Lab (Not for Health Decisions)</strong>
          <p>
            These algorithmic prototypes were trained on unverified academic dataset labels and synthetic literature distributions.
            They are strictly for computer vision and tabular machine learning engineering evaluation; they are <strong>NOT</strong> medical diagnoses and cannot prescribe treatment.
            If you are experiencing acute physical distress or medical emergency:
            <button
              type="button"
              className={styles.emergencyLink}
              onClick={onOpenEmergencyModal}
            >
              Get Emergency Help Immediately
            </button>
          </p>
        </div>
      </div>

      {/* 2. Header and Navigation */}
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>Experimental Machine Learning Lab</h2>
          <p className={styles.subtitle}>
            Explore XGBoost, LightGBM, reference-table keyword ranking, and MobileNetV2 edge classification models.
          </p>
        </div>
        <button type="button" className={styles.backBtn} onClick={onBackToDashboard}>
          <ArrowLeft size={16} /> Back to Dashboard
        </button>
      </div>

      {errorMsg && (
        <div style={{ padding: '0.75rem 1rem', background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: '8px', color: '#b91c1c' }}>
          {errorMsg}
        </div>
      )}

      {/* 3. Navigation Tabs */}
      <div className={styles.tabs}>
        <button
          type="button"
          className={`${styles.tabBtn} ${activeTab === 'graphs' ? styles.activeTabBtn : ''}`}
          onClick={() => setActiveTab('graphs')}
        >
          <BarChart3 size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
          Model Graphs & Benchmarks
        </button>
        <button
          type="button"
          className={`${styles.tabBtn} ${activeTab === 'tabular' ? styles.activeTabBtn : ''}`}
          onClick={() => setActiveTab('tabular')}
        >
          <Activity size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
          Tabular Lab Values
        </button>
        <button
          type="button"
          className={`${styles.tabBtn} ${activeTab === 'keywords' ? styles.activeTabBtn : ''}`}
          onClick={() => setActiveTab('keywords')}
        >
          <Layers size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
          Symptom Keywords
        </button>
        <button
          type="button"
          className={`${styles.tabBtn} ${activeTab === 'image' ? styles.activeTabBtn : ''}`}
          onClick={() => setActiveTab('image')}
        >
          <ImageIcon size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
          Image Classification
        </button>
        <button
          type="button"
          className={`${styles.tabBtn} ${activeTab === 'cards' ? styles.activeTabBtn : ''}`}
          onClick={() => setActiveTab('cards')}
        >
          <FileCode size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
          Model Cards & Metrics
        </button>
      </div>

      {/* 4. Tab Contents */}

      {/* TAB 0: Model Graphs & Benchmarks */}
      {activeTab === 'graphs' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className={styles.card}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', color: 'var(--color-primary-dark)' }}>
                  Empirical ML Benchmark Results
                </h3>
                <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.875rem' }}>
                  Visualization results generated directly from our verified tabular gradient boosting and MobileNetV2 edge models.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.78rem', background: '#dcfce7', color: '#166534', padding: '0.3rem 0.65rem', borderRadius: '12px', fontWeight: 600 }}>
                  13 Models Verified
                </span>
                <span style={{ fontSize: '0.78rem', background: '#e0f2fe', color: '#0369a1', padding: '0.3rem 0.65rem', borderRadius: '12px', fontWeight: 600 }}>
                  TFLite Edge Latency ~3.8ms
                </span>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '1.5rem' }}>
            {/* Graph 1 */}
            <div className={styles.card} style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div>
                  <h4 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--color-text-primary)' }}>
                    1. Model Accuracy Comparison (All 13 Models)
                  </h4>
                  <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
                    Tabular full-feature vs symptom-only vs 7 MobileNetV2 regional vision classifiers.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedGraphModal({
                    title: 'Model Accuracy Comparison',
                    src: '/graphs/01_model_accuracy_comparison.png',
                    desc: 'Cross-model accuracy audit on held-out test splits. Demonstrates tabular full (99.88%), tabular symptom-only (79.87%), and vision architectures (81.0% - 99.7%).'
                  })}
                  style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', fontWeight: 600 }}
                >
                  <Maximize2 size={13} /> Full View
                </button>
              </div>

              <div
                style={{ background: '#f8fafc', borderRadius: '8px', overflow: 'hidden', border: '1px solid #e2e8f0', cursor: 'pointer' }}
                onClick={() => setSelectedGraphModal({
                  title: 'Model Accuracy Comparison',
                  src: '/graphs/01_model_accuracy_comparison.png',
                  desc: 'Cross-model accuracy audit on held-out test splits. Demonstrates tabular full (99.88%), tabular symptom-only (79.87%), and vision architectures (81.0% - 99.7%).'
                })}
              >
                <img
                  src="/graphs/01_model_accuracy_comparison.png"
                  alt="Model Accuracy Comparison"
                  style={{ width: '100%', height: 'auto', display: 'block' }}
                />
              </div>
              <div style={{ marginTop: '0.75rem', padding: '0.5rem 0.75rem', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', fontSize: '0.8rem', color: '#166534' }}>
                <strong>Key Takeaway:</strong> Realistic symptom-only models avoid biomarker leakage while maintaining ~80% accuracy.
              </div>
            </div>

            {/* Graph 2 */}
            <div className={styles.card} style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div>
                  <h4 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--color-text-primary)' }}>
                    2. Precision, Recall & Macro-F1 Breakdown
                  </h4>
                  <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
                    Evaluation of rare class sensitivity and class imbalance effects across all targets.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedGraphModal({
                    title: 'Precision, Recall and F1 Score Comparison',
                    src: '/graphs/02_precision_recall_f1_comparison.png',
                    desc: 'Multi-metric breakdown highlighting class balance and boundary trade-offs across tabular and image classification tasks.'
                  })}
                  style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', fontWeight: 600 }}
                >
                  <Maximize2 size={13} /> Full View
                </button>
              </div>

              <div
                style={{ background: '#f8fafc', borderRadius: '8px', overflow: 'hidden', border: '1px solid #e2e8f0', cursor: 'pointer' }}
                onClick={() => setSelectedGraphModal({
                  title: 'Precision, Recall and F1 Score Comparison',
                  src: '/graphs/02_precision_recall_f1_comparison.png',
                  desc: 'Multi-metric breakdown highlighting class balance and boundary trade-offs across tabular and image classification tasks.'
                })}
              >
                <img
                  src="/graphs/02_precision_recall_f1_comparison.png"
                  alt="Precision, Recall and F1 Comparison"
                  style={{ width: '100%', height: 'auto', display: 'block' }}
                />
              </div>
              <div style={{ marginTop: '0.75rem', padding: '0.5rem 0.75rem', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '6px', fontSize: '0.8rem', color: '#1e40af' }}>
                <strong>Key Takeaway:</strong> Macro-F1 metrics strictly penalize rare-class misclassifications, ensuring transparent reporting.
              </div>
            </div>

            {/* Graph 3 */}
            <div className={styles.card} style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div>
                  <h4 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--color-text-primary)' }}>
                    3. MedScan CV Performance & Shortcut Gap Audit
                  </h4>
                  <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
                    Rigorous source shortcut detection (hair signs, nails, eyes, lips, tongue).
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedGraphModal({
                    title: 'MedScan CV Performance & Shortcut Gap',
                    src: '/graphs/03_medscan_cv_performance.png',
                    desc: 'Audit evaluating genuine anatomical signal vs background dataset artifacts across regional computer vision models.'
                  })}
                  style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', fontWeight: 600 }}
                >
                  <Maximize2 size={13} /> Full View
                </button>
              </div>

              <div
                style={{ background: '#f8fafc', borderRadius: '8px', overflow: 'hidden', border: '1px solid #e2e8f0', cursor: 'pointer' }}
                onClick={() => setSelectedGraphModal({
                  title: 'MedScan CV Performance & Shortcut Gap',
                  src: '/graphs/03_medscan_cv_performance.png',
                  desc: 'Audit evaluating genuine anatomical signal vs background dataset artifacts across regional computer vision models.'
                })}
              >
                <img
                  src="/graphs/03_medscan_cv_performance.png"
                  alt="MedScan CV Performance & Shortcut Gap"
                  style={{ width: '100%', height: 'auto', display: 'block' }}
                />
              </div>
              <div style={{ marginTop: '0.75rem', padding: '0.5rem 0.75rem', background: '#fef3c7', border: '1px solid #fde68a', borderRadius: '6px', fontSize: '0.8rem', color: '#92400e' }}>
                <strong>Key Takeaway:</strong> Hair and Nails models show genuine anatomical feature learning with minimal shortcut gap.
              </div>
            </div>

            {/* Graph 4 */}
            <div className={styles.card} style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div>
                  <h4 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--color-text-primary)' }}>
                    4. Edge Inference Latency (TFLite vs Keras)
                  </h4>
                  <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
                    CPU inference benchmark demonstrating ~45x speedup using Float32 TFLite.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedGraphModal({
                    title: 'Inference Latency Benchmark',
                    src: '/graphs/04_inference_latency.png',
                    desc: 'Benchmarked across 100 warm-up runs: MobileNetV2 Keras (~170ms) vs TensorFlow Lite Interpreter (~3.8ms).'
                  })}
                  style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', fontWeight: 600 }}
                >
                  <Maximize2 size={13} /> Full View
                </button>
              </div>

              <div
                style={{ background: '#f8fafc', borderRadius: '8px', overflow: 'hidden', border: '1px solid #e2e8f0', cursor: 'pointer' }}
                onClick={() => setSelectedGraphModal({
                  title: 'Inference Latency Benchmark',
                  src: '/graphs/04_inference_latency.png',
                  desc: 'Benchmarked across 100 warm-up runs: MobileNetV2 Keras (~170ms) vs TensorFlow Lite Interpreter (~3.8ms).'
                })}
              >
                <img
                  src="/graphs/04_inference_latency.png"
                  alt="Inference Latency Benchmark"
                  style={{ width: '100%', height: 'auto', display: 'block' }}
                />
              </div>
              <div style={{ marginTop: '0.75rem', padding: '0.5rem 0.75rem', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', fontSize: '0.8rem', color: '#166534' }}>
                <strong>Key Takeaway:</strong> TFLite enables real-time edge image triage with sub-4ms response time without GPU.
              </div>
            </div>

            {/* Graph 5 (Tabular Confusion Matrices) */}
            <div className={styles.card} style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div>
                  <h4 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--color-text-primary)' }}>
                    5A. Tabular Confusion Matrices
                  </h4>
                  <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
                    Confusion matrix heatmaps for XGBoost and LightGBM across all target deficiencies.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedGraphModal({
                    title: 'Tabular Confusion Matrices',
                    src: '/graphs/05_confusion_matrices_tabular.png',
                    desc: 'Normalized classification matrices showing true positive rates along the diagonal for both gradient boosting engines.'
                  })}
                  style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', fontWeight: 600 }}
                >
                  <Maximize2 size={13} /> Full View
                </button>
              </div>

              <div
                style={{ background: '#f8fafc', borderRadius: '8px', overflow: 'hidden', border: '1px solid #e2e8f0', cursor: 'pointer' }}
                onClick={() => setSelectedGraphModal({
                  title: 'Tabular Confusion Matrices',
                  src: '/graphs/05_confusion_matrices_tabular.png',
                  desc: 'Normalized classification matrices showing true positive rates along the diagonal for both gradient boosting engines.'
                })}
              >
                <img
                  src="/graphs/05_confusion_matrices_tabular.png"
                  alt="Tabular Confusion Matrices"
                  style={{ width: '100%', height: 'auto', display: 'block' }}
                />
              </div>
            </div>

            {/* Graph 6 (Vision Confusion Matrices) */}
            <div className={styles.card} style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div>
                  <h4 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--color-text-primary)' }}>
                    5B. Vision Regional Confusion Matrices
                  </h4>
                  <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
                    MobileNetV2 classification matrices across all 7 regional vision checkpoints.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedGraphModal({
                    title: 'Vision Confusion Matrices',
                    src: '/graphs/05_confusion_matrices_vision.png',
                    desc: 'Multi-class visual confusion grids for Eyes, Lips, Tongue, Hair, Nails, Skin, and Combined models.'
                  })}
                  style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', fontWeight: 600 }}
                >
                  <Maximize2 size={13} /> Full View
                </button>
              </div>

              <div
                style={{ background: '#f8fafc', borderRadius: '8px', overflow: 'hidden', border: '1px solid #e2e8f0', cursor: 'pointer' }}
                onClick={() => setSelectedGraphModal({
                  title: 'Vision Confusion Matrices',
                  src: '/graphs/05_confusion_matrices_vision.png',
                  desc: 'Multi-class visual confusion grids for Eyes, Lips, Tongue, Hair, Nails, Skin, and Combined models.'
                })}
              >
                <img
                  src="/graphs/05_confusion_matrices_vision.png"
                  alt="Vision Confusion Matrices"
                  style={{ width: '100%', height: 'auto', display: 'block' }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal for full-resolution graph inspection */}
      {selectedGraphModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.75)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1.5rem',
            backdropFilter: 'blur(4px)',
          }}
          onClick={() => setSelectedGraphModal(null)}
        >
          <div
            style={{
              background: '#ffffff',
              borderRadius: '16px',
              maxWidth: '1000px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '1.5rem',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem' }}>{selectedGraphModal.title}</h3>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: '#64748b' }}>
                  {selectedGraphModal.desc}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedGraphModal(null)}
                style={{
                  background: '#f1f5f9',
                  border: 'none',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 700,
                }}
              >
                Close ✕
              </button>
            </div>
            <img
              src={selectedGraphModal.src}
              alt={selectedGraphModal.title}
              style={{ width: '100%', height: 'auto', borderRadius: '8px', border: '1px solid #e2e8f0' }}
            />
          </div>
        </div>
      )}

      {/* TAB 1: Tabular Lab Values */}
      {activeTab === 'tabular' && (
        <div className={styles.card}>
          <h3 style={{ marginTop: 0, marginBottom: '0.5rem' }}>Biomarker & Demographic Consensus</h3>
          <p style={{ color: '#64748b', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
            Tests both XGBoost and LightGBM classifiers against serum blood values and reported symptoms to evaluate algorithm consensus.
          </p>

          <form onSubmit={handleTabularSubmit}>
            <div className={styles.formGrid}>
              <div className={styles.fieldGroup}>
                <label className={styles.label}>Age (18-120)</label>
                <input
                  type="number"
                  className={styles.input}
                  value={tabularForm.age}
                  min={18}
                  max={120}
                  onChange={(e) => setTabularForm({ ...tabularForm, age: parseFloat(e.target.value) || 18 })}
                />
              </div>

              <div className={styles.fieldGroup}>
                <label className={styles.label}>BMI (10-65)</label>
                <input
                  type="number"
                  step="0.1"
                  className={styles.input}
                  value={tabularForm.bmi}
                  onChange={(e) => setTabularForm({ ...tabularForm, bmi: parseFloat(e.target.value) || 20 })}
                />
              </div>

              <div className={styles.fieldGroup}>
                <label className={styles.label}>Hemoglobin (g/dL)</label>
                <input
                  type="number"
                  step="0.1"
                  className={styles.input}
                  value={tabularForm.hemoglobin_g_dl}
                  onChange={(e) => setTabularForm({ ...tabularForm, hemoglobin_g_dl: parseFloat(e.target.value) || 12 })}
                />
              </div>

              <div className={styles.fieldGroup}>
                <label className={styles.label}>Serum Vitamin D (ng/mL)</label>
                <input
                  type="number"
                  step="0.1"
                  className={styles.input}
                  value={tabularForm.serum_vitamin_d_ng_ml}
                  onChange={(e) => setTabularForm({ ...tabularForm, serum_vitamin_d_ng_ml: parseFloat(e.target.value) || 20 })}
                />
              </div>

              <div className={styles.fieldGroup}>
                <label className={styles.label}>Serum Vitamin B12 (pg/mL)</label>
                <input
                  type="number"
                  className={styles.input}
                  value={tabularForm.serum_vitamin_b12_pg_ml}
                  onChange={(e) => setTabularForm({ ...tabularForm, serum_vitamin_b12_pg_ml: parseFloat(e.target.value) || 300 })}
                />
              </div>

              <div className={styles.fieldGroup}>
                <label className={styles.label}>Serum Folate (ng/mL)</label>
                <input
                  type="number"
                  step="0.1"
                  className={styles.input}
                  value={tabularForm.serum_folate_ng_ml}
                  onChange={(e) => setTabularForm({ ...tabularForm, serum_folate_ng_ml: parseFloat(e.target.value) || 6 })}
                />
              </div>

              <div className={styles.fieldGroup}>
                <label className={styles.label}>Has Fatigue?</label>
                <select
                  className={styles.select}
                  value={tabularForm.has_fatigue}
                  onChange={(e) => setTabularForm({ ...tabularForm, has_fatigue: parseInt(e.target.value, 10) })}
                >
                  <option value={0}>No (0)</option>
                  <option value={1}>Yes (1)</option>
                </select>
              </div>

              <div className={styles.fieldGroup}>
                <label className={styles.label}>Has Bleeding Gums?</label>
                <select
                  className={styles.select}
                  value={tabularForm.has_bleeding_gums}
                  onChange={(e) => setTabularForm({ ...tabularForm, has_bleeding_gums: parseInt(e.target.value, 10) })}
                >
                  <option value={0}>No (0)</option>
                  <option value={1}>Yes (1)</option>
                </select>
              </div>
            </div>

            <button type="submit" className={styles.submitBtn} disabled={loading}>
              {loading ? 'Evaluating Model Consensus...' : 'Run Tabular Prediction'}
            </button>
          </form>

          {tabularResult && (
            <div className={styles.resultBox}>
              <h4 className={styles.resultTitle}>Model Consensus Output</h4>
              <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
                <div>
                  <span style={{ fontSize: '0.8rem', color: '#64748b' }}>XGBoost Classification:</span>
                  <p style={{ margin: '0.2rem 0', fontWeight: 700, fontSize: '1.1rem' }}>{tabularResult.xgboost_label}</p>
                </div>
                <div>
                  <span style={{ fontSize: '0.8rem', color: '#64748b' }}>LightGBM Classification:</span>
                  <p style={{ margin: '0.2rem 0', fontWeight: 700, fontSize: '1.1rem' }}>{tabularResult.lightgbm_label}</p>
                </div>
                <div>
                  <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Algorithms Agree:</span>
                  <p style={{ margin: '0.2rem 0' }}>
                    {tabularResult.models_agree ? (
                      <span className={styles.badgeSuccess}>Agreement (Consensus)</span>
                    ) : (
                      <span className={styles.badgeWarning}>Discrepancy (Divergence)</span>
                    )}
                  </p>
                </div>
              </div>
              <p className={styles.disclaimerText}>{tabularResult.warning}</p>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Symptom Keywords */}
      {activeTab === 'keywords' && (
        <div className={styles.card}>
          <h3 style={{ marginTop: 0, marginBottom: '0.5rem' }}>Reference Table Keyword-to-Nutrient Mapping</h3>
          <p style={{ color: '#64748b', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
            Trained strictly on the 116 curated expert reference table rows. Ranks matching nutrient deficiency categories based on anatomical region and character n-grams.
          </p>

          <form onSubmit={handleKeywordSubmit}>
            <div className={styles.formGrid}>
              <div className={styles.fieldGroup}>
                <label className={styles.label}>Body Region</label>
                <select
                  className={styles.select}
                  value={keywordRegion}
                  onChange={(e) => setKeywordRegion(e.target.value)}
                >
                  <option value="Eyes">Eyes</option>
                  <option value="Hair">Hair</option>
                  <option value="Lips">Lips</option>
                  <option value="Nails">Nails</option>
                  <option value="Skin">Skin</option>
                  <option value="Tongue">Tongue</option>
                </select>
              </div>

              <div className={styles.fieldGroup} style={{ gridColumn: 'span 2' }}>
                <label className={styles.label}>Symptom Keywords</label>
                <input
                  type="text"
                  className={styles.input}
                  value={keywordText}
                  placeholder="e.g. atrophic glossitis, smooth tongue, taste loss"
                  onChange={(e) => setKeywordText(e.target.value)}
                />
              </div>
            </div>

            <button type="submit" className={styles.submitBtn} disabled={loading}>
              {loading ? 'Ranking Reference Table...' : 'Find Nutrient Associations'}
            </button>
          </form>

          {keywordResult && (
            <div className={styles.resultBox}>
              <h4 className={styles.resultTitle}>Top Ranked Nutrient Groups</h4>
              <ol style={{ margin: '0.5rem 0', paddingLeft: '1.25rem' }}>
                {keywordResult.top_ranked_nutrient_groups.map((grp: string, idx: number) => (
                  <li key={idx} style={{ fontWeight: 600, margin: '0.25rem 0' }}>
                    {grp.replace(/_/g, ' ')}
                  </li>
                ))}
              </ol>
              <p className={styles.disclaimerText}>{keywordResult.reference_warning}</p>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Image Classification */}
      {activeTab === 'image' && (
        <div className={styles.card}>
          <h3 style={{ marginTop: 0, marginBottom: '0.5rem' }}>Edge Vision Classification (Float32 TFLite)</h3>
          <p style={{ color: '#64748b', fontSize: '0.875rem', marginBottom: '1rem' }}>
            Executes inference via genuine MobileNetV2 TensorFlow Lite Interpreter on local CPU. Returns top-3 ranked dataset class labels (no probability percentages).
          </p>

          <div style={{ padding: '0.6rem 0.85rem', background: '#f1f5f9', borderLeft: '4px solid #64748b', borderRadius: '4px', marginBottom: '1.25rem', fontSize: '0.85rem', color: '#334155' }}>
            <strong>Scope Caveat:</strong> Dataset-group classifier, not a deficiency detector.
          </div>

          <form onSubmit={handleImageSubmit}>
            <div className={styles.formGrid}>
              <div className={styles.fieldGroup}>
                <label className={styles.label}>Target Vision Model</label>
                <select
                  className={styles.select}
                  value={imageModel}
                  onChange={(e) => setImageModel(e.target.value)}
                >
                  <option value="combined">Combined 11-Vitamin Model</option>
                  <option value="eyes">Eyes Deficiency Model</option>
                  <option value="hair">Hair Signs Model</option>
                  <option value="nails">Nails Condition Model</option>
                  <option value="skin">Skin Deficiency Model</option>
                  <option value="tongue">Tongue Condition Model</option>
                </select>
                {(imageModel === 'eyes' || imageModel === 'skin') && (
                  <div style={{ marginTop: '0.4rem', padding: '0.35rem 0.65rem', background: '#fef3c7', color: '#92400e', borderRadius: '4px', fontSize: '0.78rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                    <AlertTriangle size={13} /> Likely dataset-source shortcut (test acc ≥ 98%)
                  </div>
                )}
                <div style={{ marginTop: '0.4rem', fontSize: '0.75rem', color: '#64748b', lineHeight: 1.4 }}>
                  <strong>What the classes really mean:</strong>{' '}
                  {imageModel === 'combined' && '7 vitamin categories (B2, C, E, K dropped due to < 100 images). Other_Nutrient_Deficiency represents heterogeneous skin/nail conditions (tinea, warts, cysts).'}
                  {imageModel === 'eyes' && 'Normal (eyelids), Vitamin_A_Deficiency (Bitot), and Other_Non_Nutritional (fundus camera glaucoma images; source shortcut).'}
                  {imageModel === 'hair' && 'Normal vs Other_Non_Nutritional (alopecia/scalp). Contains NO nutritional deficiency class.'}
                  {imageModel === 'nails' && 'Nutritional (126 koilonychia images) vs Other_Non_Nutritional (600 fungal/dystrophy images).'}
                  {imageModel === 'skin' && 'Normal vs Other_Non_Nutritional (600 web dermatology images). Contains NO nutritional deficiency class.'}
                  {imageModel === 'tongue' && 'Healthy, Diabetes, OralCancer, and Other_TCM_Tongue (600 Traditional Chinese Medicine images from shezhen dataset).'}
                </div>
              </div>

              <div className={styles.fieldGroup} style={{ gridColumn: 'span 2' }}>
                <label className={styles.label}>Upload Test Image (JPEG/PNG/WEBP, Max 5 MB)</label>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className={styles.input}
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setSelectedFile(e.target.files[0]);
                    }
                  }}
                />
              </div>
            </div>

            <button type="submit" className={styles.submitBtn} disabled={loading || !selectedFile}>
              <UploadCloud size={16} />
              {loading ? 'Running TFLite Inference...' : 'Classify Image'}
            </button>
          </form>

          {imageResult && (
            <div className={styles.resultBox}>
              <h4 className={styles.resultTitle}>Top-3 Predicted Class Labels</h4>
              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', margin: '0.5rem 0' }}>
                {imageResult.top_3_classes.map((cls: string, idx: number) => (
                  <span
                    key={idx}
                    style={{
                      padding: '0.35rem 0.75rem',
                      background: '#e0e7ff',
                      color: '#3730a3',
                      borderRadius: '6px',
                      fontWeight: 600,
                      fontSize: '0.9rem',
                    }}
                  >
                    #{idx + 1}: {cls.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
              <p className={styles.disclaimerText}>{imageResult.warning}</p>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: Model Cards & Metrics */}
      {activeTab === 'cards' && (
        <div className={styles.card}>
          <h3 style={{ marginTop: 0, marginBottom: '0.5rem' }}>Model Cards, Verification Metrics & Disclaimers</h3>
          <p style={{ color: '#64748b', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
            Inspect genuine empirical evaluations, confusion matrices, and data provenance warnings for all deployed models.
          </p>

          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
            {/* Card Selector List */}
            <div style={{ width: '260px', borderRight: '1px solid #e5e7eb', paddingRight: '1rem' }}>
              <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>
                Select Model
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', marginTop: '0.5rem' }}>
                {modelCards.map((c) => (
                  <button
                    key={c.card_id}
                    type="button"
                    style={{
                      textAlign: 'left',
                      padding: '0.5rem 0.75rem',
                      background: selectedCard?.model_id === c.model_id ? '#e0e7ff' : '#f8fafc',
                      border: '1px solid #e2e8f0',
                      borderRadius: '6px',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                    onClick={() => loadCardDetail(c.card_id)}
                  >
                    {c.model_id}
                  </button>
                ))}
              </div>
            </div>

            {/* Card Detail Viewer */}
            <div style={{ flex: 1, minWidth: '300px' }}>
              {selectedCard ? (
                <div>
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1.15rem' }}>{selectedCard.model_id}</h4>
                  <p style={{ margin: '0 0 1rem 0', color: '#4b5563', fontSize: '0.875rem' }}>
                    {selectedCard.description}
                  </p>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
                    <div style={{ padding: '0.5rem', background: '#f1f5f9', borderRadius: '6px' }}>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Architecture</span>
                      <p style={{ margin: '0.2rem 0', fontWeight: 600, fontSize: '0.85rem' }}>{selectedCard.architecture || 'Gradient Boosting'}</p>
                    </div>
                    {selectedCard.test_metrics && (
                      <>
                        <div style={{ padding: '0.5rem', background: '#f1f5f9', borderRadius: '6px' }}>
                          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Test Accuracy</span>
                          <p style={{ margin: '0.2rem 0', fontWeight: 600, fontSize: '0.85rem' }}>
                            {(selectedCard.test_metrics.accuracy * 100).toFixed(2)}%
                          </p>
                        </div>
                        <div style={{ padding: '0.5rem', background: '#f1f5f9', borderRadius: '6px' }}>
                          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Test Macro-F1</span>
                          <p style={{ margin: '0.2rem 0', fontWeight: 600, fontSize: '0.85rem' }}>
                            {selectedCard.test_metrics.macro_f1}
                          </p>
                        </div>
                      </>
                    )}
                  </div>

                  {selectedCard.tflite_verification && (
                    <div style={{ marginBottom: '1rem', padding: '0.75rem', background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: '6px' }}>
                      <strong style={{ fontSize: '0.85rem', color: '#065f46' }}>TFLite Edge Verification</strong>
                      <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8rem', color: '#047857' }}>
                        Top-1 Parity Agreement: {selectedCard.tflite_verification.top1_agreement_pct}% ·
                        Max Discrepancy: {selectedCard.tflite_verification.max_abs_difference} ·
                        Size: {selectedCard.tflite_verification.file_size_mb} MB
                      </p>
                    </div>
                  )}

                  <div style={{ padding: '0.75rem', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '6px' }}>
                    <strong style={{ fontSize: '0.85rem', color: '#92400e' }}>Data Provenance & Safety Warning</strong>
                    <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8rem', color: '#78350f' }}>
                      {selectedCard.data_provenance_warning || selectedCard.academic_disclaimer || selectedCard.strictly_reference_warning}
                    </p>
                  </div>
                </div>
              ) : (
                <p style={{ color: '#64748b' }}>Select a model card from the list to view its metrics.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
