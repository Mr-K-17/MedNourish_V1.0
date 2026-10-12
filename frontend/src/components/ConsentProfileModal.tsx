import React, { useState } from 'react';
import { ShieldCheck, UserCheck, AlertCircle } from 'lucide-react';
import styles from './ConsentProfileModal.module.css';

interface ConsentProfileModalProps {
  idToken: string;
  onProfileCreated: () => void;
}

export const ConsentProfileModal: React.FC<ConsentProfileModalProps> = ({
  idToken,
  onProfileCreated,
}) => {
  const [isAdultConfirmed, setIsAdultConfirmed] = useState(false);
  const [consentAgreed, setConsentAgreed] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [gender, setGender] = useState('');
  const [heightCm, setHeightCm] = useState('');
  const [weightKg, setWeightKg] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAdultConfirmed) {
      setErrorMsg('You must explicitly confirm you are an adult aged 18 or above (SAF-10).');
      return;
    }
    if (!consentAgreed) {
      setErrorMsg('You must review and agree to the educational prototype consent terms.');
      return;
    }

    setErrorMsg(null);
    setSubmitting(true);

    try {
      const payload = {
        is_adult_confirmed: isAdultConfirmed,
        terms_consent_version: 'v1.0',
        display_name: displayName.trim() || undefined,
        gender: gender || undefined,
        height_cm: heightCm ? parseFloat(heightCm) : undefined,
        weight_kg: weightKg ? parseFloat(weightKg) : undefined,
      };

      const res = await fetch('http://127.0.0.1:8000/v1/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: json_payload(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to save profile and consent.');
      }

      onProfileCreated();
    } catch (err: unknown) {
      const error = err as Error;
      setErrorMsg(error.message || 'Error recording consent.');
    } finally {
      setSubmitting(false);
    }
  };

  function json_payload(data: unknown): string {
    return JSON.stringify(data);
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <ShieldCheck size={28} className={styles.shieldIcon} />
        <div>
          <h2 className={styles.title}>18+ Confirmation & Educational Consent</h2>
          <p className={styles.subtitle}>
            Required before any feature use. We collect minimum data and never store date of birth.
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className={styles.errorAlert} role="alert">
          <AlertCircle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.termsBox}>
          <h3 className={styles.termsHeading}>Educational Prototype Terms (v1.0)</h3>
          <p className={styles.termsText}>
            MEDNOURISH is an academic educational prototype. Outputs are reference-table matches and
            general health information — <strong>not medical diagnoses, predictions, or prescriptions</strong>.
            This service does not replace consultation with a qualified medical professional.
          </p>
        </div>

        {/* Explicit, not pre-ticked 18+ adult confirmation per SAF-10, C-01 */}
        <label className={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={isAdultConfirmed}
            onChange={(e) => setIsAdultConfirmed(e.target.checked)}
            required
            className={styles.checkbox}
          />
          <span>
            <strong>I explicitly confirm that I am an adult aged 18 or above.</strong> (MEDNOURISH is
            strictly for adult use; date of birth is never collected).
          </span>
        </label>

        {/* Explicit consent agreement */}
        <label className={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={consentAgreed}
            onChange={(e) => setConsentAgreed(e.target.checked)}
            required
            className={styles.checkbox}
          />
          <span>
            I understand and accept the educational prototype terms and privacy policy.
          </span>
        </label>

        <hr className={styles.divider} />

        <h3 className={styles.optionalHeading}>Optional Profile Attributes (Minimal Data)</h3>
        <p className={styles.optionalSub}>
          All demographic fields below are entirely optional (C-21). You can leave them blank.
        </p>

        <div className={styles.fieldGrid}>
          <div className={styles.field}>
            <label htmlFor="display-name" className={styles.fieldLabel}>
              Display Name (Optional)
            </label>
            <input
              id="display-name"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className={styles.input}
              placeholder="e.g. Alex"
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="gender-select" className={styles.fieldLabel}>
              Gender (Optional)
            </label>
            <select
              id="gender-select"
              value={gender}
              onChange={(e) => setGender(e.target.value)}
              className={styles.input}
            >
              <option value="">Prefer not to say</option>
              <option value="female">Female</option>
              <option value="male">Male</option>
              <option value="non_binary">Non-binary</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className={styles.field}>
            <label htmlFor="height-cm" className={styles.fieldLabel}>
              Height in cm (Optional)
            </label>
            <input
              id="height-cm"
              type="number"
              min="50"
              max="280"
              value={heightCm}
              onChange={(e) => setHeightCm(e.target.value)}
              className={styles.input}
              placeholder="175"
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="weight-kg" className={styles.fieldLabel}>
              Weight in kg (Optional)
            </label>
            <input
              id="weight-kg"
              type="number"
              min="20"
              max="450"
              value={weightKg}
              onChange={(e) => setWeightKg(e.target.value)}
              className={styles.input}
              placeholder="70"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting || !isAdultConfirmed || !consentAgreed}
          className={styles.submitBtn}
        >
          <UserCheck size={18} />
          {submitting ? 'Saving Profile...' : 'Confirm & Proceed to Dashboard'}
        </button>
      </form>
    </div>
  );
};
