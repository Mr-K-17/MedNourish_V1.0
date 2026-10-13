import React, { useState, useEffect } from 'react';
import {
  HelpCircle,
  ArrowLeft,
  Volume2,
  VolumeX,
  ShieldAlert,
  Info,
  ChevronRight,
  BookOpen,
  ArrowUpRight,
} from 'lucide-react';
import styles from './NurseBotView.module.css';

interface HelpTopicSummary {
  id: string;
  category: string;
  title: string;
  summary: string;
  is_safety_refusal: boolean;
}

interface HelpTopicDetail extends HelpTopicSummary {
  content: string;
  related_actions: string[];
  disclaimer: string;
}

interface HelpMenuResponse {
  categories: string[];
  topics: HelpTopicSummary[];
  disclaimer: string;
}

interface NurseBotViewProps {
  idToken: string;
  onBackToDashboard: () => void;
  onOpenEmergencyModal?: () => void;
  onNavigateToView?: (view: 'dashboard' | 'symptom-explorer' | 'reports' | 'medbot' | 'careplan') => void;
}

export const NurseBotView: React.FC<NurseBotViewProps> = ({
  idToken,
  onBackToDashboard,
  onOpenEmergencyModal,
  onNavigateToView,
}) => {
  const [menu, setMenu] = useState<HelpMenuResponse | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null);
  const [topicDetail, setTopicDetail] = useState<HelpTopicDetail | null>(null);
  const [isLoadingMenu, setIsLoadingMenu] = useState<boolean>(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);

  useEffect(() => {
    fetchMenu();
  }, [idToken]);

  useEffect(() => {
    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const fetchMenu = async () => {
    setIsLoadingMenu(true);
    setErrorMessage(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/nursebot/menu', {
        headers: {
          Authorization: `Bearer ${idToken}`,
        },
      });
      if (res.ok) {
        const data: HelpMenuResponse = await res.json();
        setMenu(data);
        if (data.topics.length > 0) {
          // Select first topic by default
          fetchTopicDetail(data.topics[0].id);
        }
      } else {
        setErrorMessage('Failed to load NurseBot help menu.');
      }
    } catch {
      setErrorMessage('Backend service unreachable. Check if API server is running.');
    } finally {
      setIsLoadingMenu(false);
    }
  };

  const fetchTopicDetail = async (topicId: string) => {
    setIsLoadingDetail(true);
    setSelectedTopicId(topicId);
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }

    try {
      const res = await fetch(`http://127.0.0.1:8000/v1/nursebot/topics/${topicId}`, {
        headers: {
          Authorization: `Bearer ${idToken}`,
        },
      });
      if (res.ok) {
        const data: HelpTopicDetail = await res.json();
        setTopicDetail(data);
      } else {
        setErrorMessage('Failed to load topic details.');
      }
    } catch {
      setErrorMessage('Unable to connect to help service.');
    } finally {
      setIsLoadingDetail(false);
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

  const handleActionClick = (actionName: string) => {
    if (actionName === 'Emergency Help' && onOpenEmergencyModal) {
      onOpenEmergencyModal();
    } else if (actionName === 'Open MedBot' && onNavigateToView) {
      onNavigateToView('medbot');
    } else if (actionName === 'Open Symptom Explorer' && onNavigateToView) {
      onNavigateToView('symptom-explorer');
    } else if (actionName === 'Open CarePlan' && onNavigateToView) {
      onNavigateToView('careplan');
    } else if (actionName === 'Open Files & Reports' && onNavigateToView) {
      onNavigateToView('reports');
    } else if (actionName === 'View Profile Settings') {
      onBackToDashboard();
    }
  };

  const filteredTopics = menu
    ? selectedCategory === 'all'
      ? menu.topics
      : menu.topics.filter((t) => t.category === selectedCategory)
    : [];

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
          <HelpCircle size={22} color="var(--color-primary)" />
          <h2 className={styles.title}>App Help & NurseBot FAQ</h2>
        </div>
      </div>

      <div className={styles.disclaimerBanner}>
        <Info size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
        <div>
          <strong>Scripted Help Guide (NURSE-01):</strong>{' '}
          {menu?.disclaimer ||
            'NurseBot provides scripted help for using the app. It does not provide medical advice or diagnoses.'}
        </div>
      </div>

      {/* Category Tabs */}
      {menu && (
        <div className={styles.tabsRow}>
          <button
            type="button"
            className={`${styles.categoryTab} ${selectedCategory === 'all' ? styles.activeTab : ''}`}
            onClick={() => setSelectedCategory('all')}
          >
            All Questions ({menu.topics.length})
          </button>
          {menu.categories.map((cat) => (
            <button
              key={cat}
              type="button"
              className={`${styles.categoryTab} ${selectedCategory === cat ? styles.activeTab : ''}`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      )}

      {errorMessage && (
        <div style={{ color: '#b91c1c', background: '#fee2e2', padding: '0.75rem', borderRadius: '6px' }}>
          {errorMessage}
        </div>
      )}

      {/* Main Grid */}
      {isLoadingMenu ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--color-text-secondary)' }}>
          Loading scripted help topics...
        </div>
      ) : (
        <div className={styles.helpGrid}>
          {/* Left Column: Topics List */}
          <div className={styles.topicsList}>
            {filteredTopics.map((topic) => {
              const isActive = topic.id === selectedTopicId;
              return (
                <button
                  key={topic.id}
                  type="button"
                  className={`${styles.topicCard} ${isActive ? styles.topicCardActive : ''} ${
                    topic.is_safety_refusal ? styles.topicCardRefusal : ''
                  }`}
                  onClick={() => fetchTopicDetail(topic.id)}
                >
                  <div className={styles.topicTitle}>
                    <span>{topic.title}</span>
                    <ChevronRight size={16} color="var(--color-text-secondary)" />
                  </div>
                  <p className={styles.topicSummary}>{topic.summary}</p>
                  {topic.is_safety_refusal && (
                    <span className={styles.refusalBadge}>Safety Boundary</span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Right Column: Topic Detail */}
          <div>
            {isLoadingDetail ? (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--color-text-secondary)' }}>
                Loading topic details...
              </div>
            ) : topicDetail ? (
              <div className={styles.detailCard}>
                <div className={styles.detailHeader}>
                  <h3 className={styles.detailTitle}>{topicDetail.title}</h3>
                  <button
                    type="button"
                    className={`${styles.listenButton} ${isSpeaking ? styles.listeningActive : ''}`}
                    onClick={() => handleSpeak(topicDetail.content)}
                  >
                    {isSpeaking ? <VolumeX size={15} /> : <Volume2 size={15} />}
                    {isSpeaking ? 'Stop' : 'Listen'}
                  </button>
                </div>

                <p className={styles.detailContent}>{topicDetail.content}</p>

                {topicDetail.is_safety_refusal && (
                  <div className={styles.refusalCallout}>
                    <ShieldAlert size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
                    <strong>Clinical Limitation Notice:</strong> NurseBot is programmed to strictly refuse medical diagnosis and drug dosing requests per medical safety rules SAF-02 and SAF-14.
                  </div>
                )}

                {topicDetail.related_actions && topicDetail.related_actions.length > 0 && (
                  <div className={styles.relatedActionsArea}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
                      Suggested Next Steps:
                    </span>
                    <div className={styles.actionsList}>
                      {topicDetail.related_actions.map((act) => (
                        <button
                          key={act}
                          type="button"
                          className={styles.actionPill}
                          onClick={() => handleActionClick(act)}
                        >
                          <ArrowUpRight size={14} /> {act}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className={styles.emptySelection}>
                <BookOpen size={36} />
                <h4 style={{ margin: 0 }}>Select a Help Question</h4>
                <p style={{ margin: 0, fontSize: '0.875rem' }}>
                  Choose any topic from the list to view scripted answers and safety guidance.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
