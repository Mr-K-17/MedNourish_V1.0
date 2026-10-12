import React from 'react';
import { AlertTriangle, PhoneCall, ArrowLeft } from 'lucide-react';
import styles from './EmergencyHelpModal.module.css';

interface EmergencyHelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const EmergencyHelpModal: React.FC<EmergencyHelpModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div
      className={styles.overlay}
      role="dialog"
      aria-modal="true"
      aria-labelledby="emergency-modal-title"
    >
      <div className={styles.modal}>
        <div className={styles.header}>
          <div className={styles.titleGroup}>
            <AlertTriangle className={styles.warningIcon} size={24} />
            <h2 id="emergency-modal-title" className={styles.title}>
              Urgent Medical & Crisis Help
            </h2>
          </div>
          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close urgent help dialog"
          >
            ✕
          </button>
        </div>

        <div className={styles.body}>
          <div className={styles.alertBox}>
            <p className={styles.alertText}>
              <strong>If you are experiencing severe chest pain, sudden breathlessness, severe bleeding, sudden weakness/numbness, or thoughts of self-harm:</strong>
            </p>
            <p className={styles.alertAction}>
              Please contact your local emergency services immediately or visit the nearest emergency department.
            </p>
          </div>

          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>
              <PhoneCall size={18} /> Emergency Contact Instructions
            </h3>
            <p className={styles.text}>
              MEDNOURISH is an educational prototype and does not provide emergency triage, immediate clinical care, or medical diagnosis.
            </p>
            <ul className={styles.list}>
              <li>Call your national or regional emergency number immediately.</li>
              <li>If you are in danger of harming yourself, call or text your local suicide & crisis lifeline right now. Free, confidential support is available 24/7.</li>
              <li>Reach out to a trusted family member, friend, or healthcare professional.</li>
            </ul>
          </div>
        </div>

        <div className={styles.footer}>
          <button type="button" className={styles.backButton} onClick={onClose}>
            <ArrowLeft size={16} /> Return to MedNourish
          </button>
        </div>
      </div>
    </div>
  );
};
