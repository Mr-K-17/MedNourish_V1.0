import React, { useState, useEffect, useRef } from 'react';
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
  Send,
  MessageSquare,
  ExternalLink,
  AlertTriangle,
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

interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  timestamp: string;
  intent?: string;
  source_name?: string;
  source_url?: string;
  is_web_answer?: boolean;
}

interface NurseBotViewProps {
  idToken: string;
  onBackToDashboard: () => void;
  onOpenEmergencyModal?: () => void;
  onNavigateToView?: (view: 'dashboard' | 'symptom-explorer' | 'reports' | 'medbot' | 'careplan') => void;
}

const QUICK_QUESTIONS = [
  'Hello! Who are you and how can you help?',
  'How does the heart pump blood through the body?',
  'Explain cellular respiration, ATP and the Krebs cycle',
  'What is the difference between innate and adaptive immunity?',
  'How do neurons and neurotransmitters work?',
  'What does the liver do in the human body?',
  'How does MedBot work?',
  'What foods have Vitamin B12 and Iron?',
];

export const NurseBotView: React.FC<NurseBotViewProps> = ({
  idToken,
  onBackToDashboard,
  onOpenEmergencyModal,
  onNavigateToView,
}) => {
  const [activeTab, setActiveTab] = useState<'chat' | 'library'>('chat');
  const [menu, setMenu] = useState<HelpMenuResponse | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null);
  const [topicDetail, setTopicDetail] = useState<HelpTopicDetail | null>(null);
  const [isLoadingMenu, setIsLoadingMenu] = useState<boolean>(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);

  // Chat State
  const [chatInput, setChatInput] = useState<string>('');
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-0',
      sender: 'bot',
      text: 'Hello! I am MedNourish NurseBot, your AI conversational and medical sciences assistant. I am trained in human anatomy, organ physiology, cellular bioenergetics, immunology, and nutritional health. What medical topic or question would you like to explore today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      intent: 'ai_chat',
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (activeTab === 'chat') {
      scrollToBottom();
    }
  }, [messages, isTyping, activeTab]);

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

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || chatInput).trim();
    if (!text || isTyping) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setChatInput('');
    setIsTyping(true);

    try {
      const res = await fetch('http://127.0.0.1:8000/v1/nursebot/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({ question: text }),
      });

      if (res.status === 429) {
        const botMsg: ChatMessage = {
          id: `bot-${Date.now()}`,
          sender: 'bot',
          text: 'Rate limit reached: Maximum 10 queries per minute. Please wait a moment before sending another inquiry.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          intent: 'refusal',
        };
        setMessages((prev) => [...prev, botMsg]);
      } else if (res.ok) {
        const data = await res.json();
        const botMsg: ChatMessage = {
          id: `bot-${Date.now()}`,
          sender: 'bot',
          text: data.reply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          intent: data.intent,
          source_name: data.source_name,
          source_url: data.source_url,
          is_web_answer: data.is_web_answer,
        };
        setMessages((prev) => [...prev, botMsg]);
      } else {
        const botMsg: ChatMessage = {
          id: `bot-${Date.now()}`,
          sender: 'bot',
          text: 'Could not reach medical reference services. Please consult a qualified clinician.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          intent: 'out_of_scope',
        };
        setMessages((prev) => [...prev, botMsg]);
      }
    } catch {
      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: 'bot',
        text: 'Network connection error. Please verify the backend API server is active.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        intent: 'out_of_scope',
      };
      setMessages((prev) => [...prev, botMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
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
          <HelpCircle size={22} color="var(--color-primary)" />
          <h2 className={styles.title}>NurseBot Assistant & App Help</h2>
        </div>
        <div className={styles.modeTabs}>
          <button
            type="button"
            className={`${styles.modeButton} ${activeTab === 'chat' ? styles.modeButtonActive : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <MessageSquare size={15} /> Chat Assistant
          </button>
          <button
            type="button"
            className={`${styles.modeButton} ${activeTab === 'library' ? styles.modeButtonActive : ''}`}
            onClick={() => setActiveTab('library')}
          >
            <BookOpen size={15} /> Scripted FAQs
          </button>
        </div>
      </div>

      {/* Prototype Safety Banner */}
      <div className={styles.disclaimerBanner}>
        <Info size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
        <div>
          <strong>Educational Prototype Notice:</strong>{' '}
          {menu?.disclaimer ||
            'NurseBot provides scripted app help and queries official NIH MedlinePlus reference fact sheets. It does not provide medical diagnoses, treatment advice, or drug dosages.'}
        </div>
      </div>

      {errorMessage && (
        <div className={styles.errorAlert}>
          {errorMessage}
        </div>
      )}

      {/* CHAT TAB (WhatsApp-Style Interface) */}
      {activeTab === 'chat' && (
        <div className={styles.chatWrapper}>
          {/* Quick-Prompt Chips */}
          <div className={styles.quickChipsBar}>
            <span className={styles.quickChipsLabel}>Quick Questions:</span>
            {QUICK_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                className={styles.quickChip}
                onClick={() => handleSendMessage(q)}
                disabled={isTyping}
              >
                {q}
              </button>
            ))}
          </div>

          {/* WhatsApp-Style Messages Container */}
          <div className={styles.messagesContainer}>
            {messages.map((msg) => {
              const isUser = msg.sender === 'user';
              const isEmergency = msg.intent === 'emergency';
              const isRefusal = msg.intent === 'refusal';

              return (
                <div
                  key={msg.id}
                  className={`${styles.messageRow} ${isUser ? styles.userRow : styles.botRow}`}
                >
                  <div
                    className={`${styles.bubble} ${
                      isUser ? styles.userBubble : styles.botBubble
                    } ${isEmergency ? styles.emergencyBubble : ''}`}
                  >
                    {!isUser && (
                      <div className={styles.bubbleHeader}>
                        <span className={styles.senderLabel}>
                          NurseBot{' '}
                          {msg.intent === 'web_reference' && '(NIH / MedlinePlus)'}
                          {msg.intent === 'medical_science' && '(Medical Sciences)'}
                          {msg.intent === 'ai_chat' && '(AI Assistant)'}
                        </span>
                        <button
                          type="button"
                          className={styles.speechIconBtn}
                          onClick={() => handleSpeak(msg.text)}
                          title="Read aloud"
                        >
                          <Volume2 size={13} />
                        </button>
                      </div>
                    )}

                    <div className={styles.messageText}>{msg.text}</div>

                    {/* Emergency Alert Box */}
                    {isEmergency && (
                      <div className={styles.emergencyBox}>
                        <AlertTriangle size={16} />
                        <div>
                          <strong>Urgent Care Redirection:</strong> If this is a life-threatening emergency, stop using software and call 911 or your local emergency line immediately.
                        </div>
                      </div>
                    )}

                    {/* Safety Refusal Notice */}
                    {isRefusal && (
                      <div className={styles.refusalBox}>
                        <ShieldAlert size={14} />
                        <span>Safety Boundary: Scripted refusal for diagnosis/dosage requests.</span>
                      </div>
                    )}

                    {/* Web Answer Source & Disclaimer (Phase 4 requirement) */}
                    {msg.is_web_answer && (
                      <div className={styles.webAnswerContainer}>
                        <div className={styles.webDisclaimer}>
                          <strong>Demo app disclaimer:</strong> This information comes from the internet and may be incomplete. Please do not rely on it; talk to a doctor or pharmacist.
                        </div>
                        {msg.source_name && (
                          <div className={styles.sourceMeta}>
                            <span>Source: {msg.source_name}</span>
                            {msg.source_url && (
                              <a
                                href={msg.source_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className={styles.sourceLink}
                              >
                                View Fact Sheet <ExternalLink size={12} />
                              </a>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    <div className={styles.timestampRow}>
                      <span className={styles.timestamp}>{msg.timestamp}</span>
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Typing Indicator */}
            {isTyping && (
              <div className={`${styles.messageRow} ${styles.botRow}`}>
                <div className={`${styles.bubble} ${styles.botBubble} ${styles.typingBubble}`}>
                  <div className={styles.typingDot} />
                  <div className={styles.typingDot} />
                  <div className={styles.typingDot} />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input Bar */}
          <div className={styles.inputArea}>
            <input
              type="text"
              className={styles.chatInputField}
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about app features or search NIH nutrition fact sheets..."
              maxLength={500}
              disabled={isTyping}
            />
            <button
              type="button"
              className={styles.sendButton}
              onClick={() => handleSendMessage()}
              disabled={!chatInput.trim() || isTyping}
            >
              <Send size={16} />
              <span>Send</span>
            </button>
          </div>
        </div>
      )}

      {/* SCRIPTED FAQ LIBRARY TAB */}
      {activeTab === 'library' && (
        <div>
          {/* Category Tabs */}
          {menu && (
            <div className={styles.tabsRow}>
              <button
                type="button"
                className={`${styles.categoryTab} ${selectedCategory === 'all' ? styles.activeTab : ''}`}
                onClick={() => setSelectedCategory('all')}
              >
                All Topics ({menu.topics.length})
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

          {isLoadingMenu ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--color-text-secondary)' }}>
              Loading scripted help topics...
            </div>
          ) : (
            <div className={styles.helpGrid} style={{ marginTop: '1rem' }}>
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
                        <strong>Clinical Limitation Notice:</strong> NurseBot strictly refuses medical diagnosis and drug dosing requests per medical safety rules SAF-02 and SAF-14.
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
      )}
    </div>
  );
};
