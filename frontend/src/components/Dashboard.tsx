import React from 'react';
import {
  Bot,
  Search,
  CalendarCheck,
  FileText,
  Clock,
  Sparkles,
  HelpCircle,
  Camera,
  Building2,
  ArrowRight,
} from 'lucide-react';
import styles from './Dashboard.module.css';

interface ModuleTile {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  phase: string;
  status: 'ready';
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
      phase: 'Interactive Consultation',
      status: 'ready',
      tag: 'Core Feature',
    },
    {
      id: 'symptom-explorer',
      title: 'Symptom Reference Explorer',
      description:
        'Browse and select anatomical symptom tags across Eyes, Lips, Tongue, Hair, Nails, and Skin to analyze nutrient associations.',
      icon: <Search size={28} className={styles.tileIcon} aria-hidden="true" />,
      phase: 'Knowledge Explorer',
      status: 'ready',
      tag: 'Reference Base',
    },
    {
      id: 'careplan',
      title: 'CarePlan Wellness Tasks & Diet',
      description:
        'Personalized daily routine with rich food recommendations, fruits to eat, dietary habits, and hydration targets.',
      icon: <CalendarCheck size={28} className={styles.tileIcon} aria-hidden="true" />,
      phase: 'Nutrition & Lifestyle',
      status: 'ready',
      tag: 'Action Plan',
    },
    {
      id: 'medscan-lite',
      title: 'MedScan-Lite Image Inspection',
      description:
        'Guided regional photo capture and edge MobileNetV2 classification detecting physical deficiency manifestations.',
      icon: <Camera size={28} className={styles.tileIcon} aria-hidden="true" />,
      phase: 'Computer Vision',
      status: 'ready',
      tag: 'Edge AI',
    },
    {
      id: 'virtual-ward',
      title: 'VirtualWard Facility Directory & Map',
      description:
        'Locate nearby hospitals and community health centers on an interactive map with direct navigation and consultation vouchers.',
      icon: <Building2 size={28} className={styles.tileIcon} aria-hidden="true" />,
      phase: 'Clinical Directory',
      status: 'ready',
      tag: 'Facility Map',
    },
    {
      id: 'reports',
      title: 'Files & Assessment Reports',
      description:
        'Timeline of saved reference match summaries, diagnostic justifications, and exportable consultation PDFs/summaries.',
      icon: <FileText size={28} className={styles.tileIcon} aria-hidden="true" />,
      phase: 'Health Records',
      status: 'ready',
      tag: 'Saved Reports',
    },
    {
      id: 'nursebot',
      title: 'NurseBot Assistant & FAQ',
      description:
        'Instant clinical guidance, FAQ assistance, and medical boundary explanations powered by curated health references.',
      icon: <HelpCircle size={28} className={styles.tileIcon} aria-hidden="true" />,
      phase: 'Assistance & FAQ',
      status: 'ready',
      tag: 'Clinical Guide',
    },
    {
      id: 'mllab',
      title: 'Experimental ML Lab',
      description:
        'Inspect model evaluation benchmarks, latency metrics, ROC curves, confusion matrices, and tabular XGBoost/LightGBM comparisons.',
      icon: <Sparkles size={28} className={styles.tileIcon} aria-hidden="true" />,
      phase: 'ML Benchmarks',
      status: 'ready',
      tag: 'Model Analytics',
    },
  ];

  return (
    <div className={styles.dashboardContainer}>
      <div className={styles.welcomeBanner}>
        <div>
          <h2 className={styles.welcomeTitle}>
            Welcome back, {displayName || 'Member'}
          </h2>
          <p className={styles.welcomeText}>
            Personalized nutritional assessment and clinical knowledge base active under consent {consentVersion || 'v2.0'}.
          </p>
        </div>
      </div>

      <div className={styles.sectionHeader}>
        <h3 className={styles.sectionTitle}>MedNourish Clinical Suite</h3>
        <span className={styles.sectionBadge}>
          <Clock size={14} /> Full Suite Active
        </span>
      </div>

      <div className={styles.grid}>
        {modules.map((m) => (
          <div
            key={m.id}
            data-tile={m.id}
            className={styles.tileCard}
            role="region"
            aria-labelledby={`tile-title-${m.id}`}
            onClick={() => onSelectTile?.(m.id)}
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
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectTile?.(m.id);
                }}
              >
                <span>Launch</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
