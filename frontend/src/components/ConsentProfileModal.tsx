import React, { useState } from 'react';
import { ShieldCheck, UserCheck, AlertCircle, Info } from 'lucide-react';
import styles from './ConsentProfileModal.module.css';

interface ConsentProfileModalProps {
  idToken: string;
  onProfileCreated: () => void;
}

const CANONICAL_CONDITIONS = [
  'Type 2 diabetes',
  'Type 1 diabetes',
  'Hypertension',
  'Anemia',
  'Thyroid disorder',
  'Asthma',
  'Celiac disease',
  "Crohn's/IBD",
  'Irritable bowel syndrome',
  'Chronic kidney disease',
  'Liver disease',
  'Heart disease',
  'PCOS',
  'Osteoporosis',
  'Depression/anxiety',
  'Migraine',
  'Acid reflux/gastritis',
  'Lactose intolerance/food allergy',
  'None',
];

const BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Unknown'];

export const ConsentProfileModal: React.FC<ConsentProfileModalProps> = ({
  idToken,
  onProfileCreated,
}) => {
  const [consentAgreed, setConsentAgreed] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [gender, setGender] = useState('');
  const [heightCm, setHeightCm] = useState('');
  const [weightKg, setWeightKg] = useState('');
  const [age, setAge] = useState('');
  const [bloodType, setBloodType] = useState('');
  const [selectedConditions, setSelectedConditions] = useState<string[]>([]);
  const [otherCondition, setOtherCondition] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const parsedAge = age ? parseInt(age, 10) : null;
  const isUnder18 = parsedAge !== null && !isNaN(parsedAge) && parsedAge < 18;

  const handleToggleCondition = (cond: string) => {
    if (cond === 'None') {
      setSelectedConditions(['None']);
      return;
    }
    const filtered = selectedConditions.filter((c) => c !== 'None');
    if (filtered.includes(cond)) {
      setSelectedConditions(filtered.filter((c) => c !== cond));
    } else {
      setSelectedConditions([...filtered, cond]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!consentAgreed) {
      setErrorMsg('You must review and agree to the educational prototype demo terms.');
      return;
    }

    if (parsedAge !== null && (parsedAge < 1 || parsedAge > 120)) {
      setErrorMsg('Age must be between 1 and 120 years.');
      return;
    }

    setErrorMsg(null);
    setSubmitting(true);

    try {
      const payload = {
        demo_consent_confirmed: true,
        is_adult_confirmed: parsedAge !== null ? parsedAge >= 18 : true,
        terms_consent_version: 'v1.0',
        display_name: displayName.trim() || undefined,
        gender: gender || undefined,
        height_cm: heightCm ? parseFloat(heightCm) : undefined,
        weight_kg: weightKg ? parseFloat(weightKg) : undefined,
        age: parsedAge !== null && !isNaN(parsedAge) ? parsedAge : undefined,
        blood_type: bloodType || undefined,
        conditions: selectedConditions.length > 0 ? selectedConditions : undefined,
        other_condition: otherCondition.trim() || undefined,
      };

      const res = await fetch('http://127.0.0.1:8000/v1/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify(payload),
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

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <ShieldCheck size={28} className={styles.shieldIcon} />
        <div>
          <h2 className={styles.title}>Educational Consent & Health Profile</h2>
          <p className={styles.subtitle}>
            MedNourish is an educational prototype. We collect minimum profile data and never ask for or store Date of Birth.
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

        {/* Demo Consent Checkbox (C-33 replaces strict 18+ gate) */}
        <label className={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={consentAgreed}
            onChange={(e) => setConsentAgreed(e.target.checked)}
            required
            className={styles.checkbox}
          />
          <span>
            <strong>I agree to the educational prototype demo terms and privacy policy.</strong> (Demo consent; date of birth is never collected).
          </span>
        </label>

        <hr className={styles.divider} />

        <h3 className={styles.optionalHeading}>Profile Attributes (C-33)</h3>
        <p className={styles.optionalSub}>
          Demographic and health attributes to enrich reference matching.
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
            <label htmlFor="age-input" className={styles.fieldLabel}>
              Age (Years: 1–120)
            </label>
            <input
              id="age-input"
              type="number"
              min="1"
              max="120"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              className={styles.input}
              placeholder="e.g. 28"
            />
            {isUnder18 && (
              <div className={styles.under18Notice}>
                <Info size={14} />
                <span>Reference content is written for adults; demo only.</span>
              </div>
            )}
          </div>

          <div className={styles.field}>
            <label htmlFor="blood-type-select" className={styles.fieldLabel}>
              Blood Type (Optional)
            </label>
            <select
              id="blood-type-select"
              value={bloodType}
              onChange={(e) => setBloodType(e.target.value)}
              className={styles.input}
            >
              <option value="">Select blood type...</option>
              {BLOOD_TYPES.map((bt) => (
                <option key={bt} value={bt}>
                  {bt}
                </option>
              ))}
            </select>
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

        {/* Canonical Conditions Selection */}
        <div className={styles.conditionsContainer}>
          <label className={styles.fieldLabel}>
            Existing Health Conditions (Select any that apply)
          </label>
          <div className={styles.conditionsGrid}>
            {CANONICAL_CONDITIONS.map((cond) => (
              <label key={cond} className={styles.conditionChip}>
                <input
                  type="checkbox"
                  checked={selectedConditions.includes(cond)}
                  onChange={() => handleToggleCondition(cond)}
                  className={styles.checkbox}
                />
                <span>{cond}</span>
              </label>
            ))}
          </div>
        </div>

        <div className={styles.field}>
          <label htmlFor="other-condition" className={styles.fieldLabel}>
            Other Condition (Optional, max 100 characters)
          </label>
          <input
            id="other-condition"
            type="text"
            maxLength={100}
            value={otherCondition}
            onChange={(e) => setOtherCondition(e.target.value)}
            className={styles.input}
            placeholder="e.g. Mild seasonal allergies"
          />
        </div>

        <button
          type="submit"
          disabled={submitting || !consentAgreed}
          className={styles.submitBtn}
        >
          <UserCheck size={18} />
          {submitting ? 'Saving Profile...' : 'Confirm & Proceed to Dashboard'}
        </button>
      </form>
    </div>
  );
};
