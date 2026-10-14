import React from 'react';
import {
  Bot,
  Search,
  CalendarCheck,
  FileText,
  Clock,
  Sparkles,
  HelpCircle,
} from 'lucide-react';
import styles from './Dashboard.module.css';

interface ModuleTile {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  phase: string;
  status: 'coming_soon' | 'ready';
  tag: string;
}

interface DashboardProps {
  displayName?: string;
  consentVersion?: string;
  onSelectTile?: (tileId: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  displayName,
  consentVersion,
  onSelectTile,
}) => {
  const modules: ModuleTile[] = [
    {
      id: 'medbot',
      title: 'MedBot Questionnaire',
      description:
        'Guided health and symptom questionnaire with Simple and Standard modes for transparent reference matching.',
      icon: <Bot size={28} className={styles.tileIcon} aria-hidden="true" />,
      phase: 'Phase 1B',
      status: 'ready',
      tag: 'Available Now',
    },
    {
      id: 'symptom-explorer',
      title: 'Symptom Reference Explorer',
      description:
        'Browse and select anatomical symptom tags to look up educational reference-table associations.',
      icon: <Search size={28} className={styles.tileIcon} aria-hidden="true" />,
      phase: 'Phase 1B',
      status: 'ready',
      tag: 'Available Now',
    },
    {
      id: 'careplan',
      title: 'CarePlan Wellness Tasks',
      description:
        'Customizable daily wellness tasks for water intake, nutrition, and exercise. No medication reminders.',
      icon: <CalendarCheck size={28} className={styles.tileIcon} aria-hidden="true" />,
      phase: 'Phase 1B',
      status: 'ready',
      tag: 'Available Now',
    },
    {
      id: 'reports',
      title: 'Files & Reports',
      description:
        'Secure timeline of saved reference match summaries with date stamps and matched tag histories.',
      icon: <FileText size={28} className={styles.tileIcon} aria-hidden="true" />,
      phase: 'Phase 1B',
      status: 'ready',
      tag: 'Available Now',
    },
    {
      id: 'nursebot',
      title: 'App Help & FAQ (NurseBot)',
      description:
        'Scripted application guidance, FAQs, and medical safety boundary explanations. No generative AI.',
      icon: <HelpCircle size={28} className={styles.tileIcon} aria-hidden="true" />,
      phase: 'Phase 1B',
      status: 'ready',
      tag: 'Available Now',
    },
    {
      id: 'mllab',
      title: 'Experimental ML Lab (not for health decisions)',
      description:
        'Algorithmic sandbox evaluating tabular models, reference keyword rankings, and MobileNetV2 edge models.',
      icon: <Sparkles size={28} className={styles.tileIcon} aria-hidden="true" />,
      phase: 'Phase 3.3',
      status: 'ready',
      tag: 'Experimental Demo',
    },
  ];

  return (
    <div className={styles.dashboardContainer}>
      <div className={styles.welcomeBanner}>
        <div>
          <h2 className={styles.welcomeTitle}>
            Hello, {displayName || 'Member'}
          </h2>
          <p className={styles.welcomeText}>
            You are signed in as a verified adult (18+) under educational consent {consentVersion || 'v1.0'}.
          </p>
        </div>
      </div>

      <div className={styles.sectionHeader}>
        <h3 className={styles.sectionTitle}>Application Modules</h3>
        <span className={styles.sectionBadge}>
          <Clock size={14} /> Phase 1B Deliverables
        </span>
      </div>

      <div className={styles.grid}>
        {modules.map((m) => (
          <div
            key={m.id}
            className={styles.tileCard}
            role="region"
            aria-labelledby={`tile-title-${m.id}`}
          >
            <div className={styles.tileHeader}>
              <div className={styles.iconWrapper}>{m.icon}</div>
              <span className={styles.statusBadge} aria-label={`Status: ${m.tag}`}>
                {m.tag}
              </span>
            </div>

            <h4 id={`tile-title-${m.id}`} className={styles.tileTitle}>
              {m.title}
            </h4>

            <p className={styles.tileDescription}>{m.description}</p>

            <div className={styles.tileFooter}>
              <span className={styles.phaseIndicator}>{m.phase}</span>
              <button
                type="button"
                className={styles.tileActionBtn}
                disabled={m.status === 'coming_soon'}
                aria-disabled={m.status === 'coming_soon'}
                onClick={() => onSelectTile?.(m.id)}
              >
                {m.status === 'ready' ? (
                  <>
                    <Search size={14} /> Launch Explorer
                  </>
                ) : (
                  <>
                    <Sparkles size={14} /> Preview (Phase 1B)
                  </>
                )}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
