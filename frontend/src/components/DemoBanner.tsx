import React from 'react';
import { AlertCircle } from 'lucide-react';
import styles from './DemoBanner.module.css';

interface DemoBannerProps {
  onLearnMore?: () => void;
}

export const DemoBanner: React.FC<DemoBannerProps> = ({ onLearnMore }) => {
  return (
    <aside className={styles.banner} role="status" aria-label="Educational demo status">
      <AlertCircle size={18} className={styles.bannerIcon} aria-hidden="true" />
      <p className={styles.bannerText}>
        <strong>Educational Prototype:</strong> MEDNOURISH results are reference-table matches and
        general health education only — never medical diagnoses, predictions, or prescriptions.
        {onLearnMore && (
          <button
            type="button"
            className={styles.bannerLink}
            onClick={onLearnMore}
            aria-haspopup="dialog"
          >
            Learn more
          </button>
        )}
      </p>
    </aside>
  );
};
