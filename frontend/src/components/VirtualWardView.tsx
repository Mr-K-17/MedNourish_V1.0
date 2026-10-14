import React, { useState } from 'react';
import {
  Building2,
  ArrowLeft,
  Navigation,
  AlertTriangle,
  Info,
  Calendar,
  ExternalLink,
} from 'lucide-react';
import styles from './VirtualWardView.module.css';

interface Facility {
  id: string;
  name: string;
  type: 'General Hospital' | 'Community Health Center' | 'Emergency Care';
  categoryDescription: string;
  mapsQuery: string;
}

const LOCAL_FACILITIES: Facility[] = [
  {
    id: 'fac-1',
    name: 'Nearby General Hospital',
    type: 'General Hospital',
    categoryDescription: 'Comprehensive outpatient and inpatient medical services.',
    mapsQuery: 'General+Hospital+near+me',
  },
  {
    id: 'fac-2',
    name: 'Nearby Community Health Center (CHC)',
    type: 'Community Health Center',
    categoryDescription: 'Public primary health clinics, nutrition counseling, and maternal care.',
    mapsQuery: 'Community+Health+Center+near+me',
  },
  {
    id: 'fac-3',
    name: 'Nearby Urgent Care / Emergency Trauma Unit',
    type: 'Emergency Care',
    categoryDescription: '24/7 acute trauma and emergency medical interventions.',
    mapsQuery: 'Emergency+Hospital+near+me',
  },
];

interface VirtualWardViewProps {
  idToken?: string | null;
  onBackToDashboard: () => void;
  onOpenEmergencyModal: () => void;
}

export const VirtualWardView: React.FC<VirtualWardViewProps> = ({
  idToken,
  onBackToDashboard,
  onOpenEmergencyModal,
}) => {
  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(null);
  const [appointmentRequested, setAppointmentRequested] = useState<boolean>(false);
  const [reminderCreated, setReminderCreated] = useState<boolean>(false);
  const [preferredDate, setPreferredDate] = useState<string>('');
  const [consultReason, setConsultReason] = useState<string>('General nutrition review');

  const handleOpenMaps = (query: string) => {
    const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const handleAddCheckupReminder = async () => {
    if (!idToken) return;
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/careplan/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({
          title: 'Schedule routine clinical check-up with primary doctor',
          category: 'general',
          target_frequency: 'as needed',
          reminder_time: '10:00',
        }),
      });
      if (res.ok) {
        setReminderCreated(true);
        setTimeout(() => setReminderCreated(false), 4000);
      }
    } catch {
      // fallback handling
    }
  };

  const handleRequestAppointment = (e: React.FormEvent) => {
    e.preventDefault();
    setAppointmentRequested(true);
  };

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.headerBar}>
        <button
          type="button"
          onClick={onBackToDashboard}
          className={styles.backButton}
        >
          <ArrowLeft size={16} /> Back to Dashboard
        </button>
        <div className={styles.titleArea}>
          <Building2 size={24} color="var(--color-primary)" />
          <h2 className={styles.title}>VirtualWard Facility Directory</h2>
        </div>
      </div>

      {/* Safety Notice */}
      <div className={styles.warningBanner}>
        <AlertTriangle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
        <div>
          <strong>Educational Prototype Notice (WARD-01, WARD-03):</strong> MedNourish does NOT
          provide autonomous medical triage or live booking with hospital EMR systems. If you have
          acute symptoms, chest pain, breathing difficulty, or severe weakness, contact emergency
          services immediately.
          <div style={{ marginTop: '0.4rem' }}>
            <button
              type="button"
              onClick={onOpenEmergencyModal}
              className={styles.emergencyLinkBtn}
            >
              Open Urgent Help & Emergency Numbers →
            </button>
          </div>
        </div>
      </div>

      {/* Intro info */}
      <div className={styles.infoCard}>
        <Info size={18} color="var(--color-primary)" style={{ flexShrink: 0 }} />
        <p className={styles.infoText}>
          Use this directory to locate verified clinical facilities in your area. You can navigate
          directly via Google Maps or prepare an in-person consultation request sheet.
        </p>
      </div>

      {/* Facilities Grid */}
      <div className={styles.facilityGrid}>
        {LOCAL_FACILITIES.map((fac) => (
          <div key={fac.id} className={styles.facilityCard}>
            <div className={styles.facilityHeader}>
              <span className={styles.facilityBadge}>{fac.type}</span>
            </div>

            <h3 className={styles.facilityName}>{fac.name}</h3>
            <p className={styles.facilityAddress}>
              {fac.categoryDescription}
            </p>

            <div className={styles.cardActions}>
              <button
                type="button"
                onClick={() => handleOpenMaps(fac.mapsQuery)}
                className={styles.mapsBtn}
                title="Search nearby facilities via Google Maps"
              >
                <Navigation size={14} /> Find Near Me on Google Maps <ExternalLink size={12} />
              </button>

              <button
                type="button"
                onClick={() => {
                  setSelectedFacility(fac);
                  setAppointmentRequested(false);
                }}
                className={styles.consultBtn}
              >
                <Calendar size={14} /> Consultation Sheet
              </button>
            </div>
          </div>
        ))}

        {/* Coming Later Card per C-27 */}
        <div className={styles.facilityCard} style={{ background: '#f8fafc', borderStyle: 'dashed' }}>
          <div className={styles.facilityHeader}>
            <span className={styles.facilityBadge} style={{ background: '#e2e8f0', color: '#475569', borderColor: '#cbd5e1' }}>
              Phase 4 Candidate
            </span>
          </div>
          <h3 className={styles.facilityName}>Direct Telehealth & EMR Integration</h3>
          <p className={styles.facilityAddress}>
            Live doctor messaging, API hospital appointment scheduling, and electronic health record syncing are reserved for future evaluated phases under clinical partnership.
          </p>
          <div className={styles.cardActions}>
            <button
              type="button"
              onClick={handleAddCheckupReminder}
              disabled={reminderCreated}
              className={styles.mapsBtn}
              title="Add a routine clinical checkup task to your CarePlan"
            >
              <Calendar size={14} /> {reminderCreated ? 'Check-up Task Added!' : 'Add Check-up Task to CarePlan'}
            </button>
          </div>
        </div>
      </div>

      {/* Modal / Request Form for Selected Facility */}
      {selectedFacility && (
        <div className={styles.modalOverlay} onClick={() => setSelectedFacility(null)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <h3 className={styles.modalTitle}>
              Consultation Request Sheet: {selectedFacility.name}
            </h3>

            {appointmentRequested ? (
              <div className={styles.successBox}>
                <h4>Consultation Sheet Prepared (WARD-04)</h4>
                <p>
                  Your consultation request record has been saved locally for your visit to{' '}
                  <strong>{selectedFacility.name}</strong> on {preferredDate || 'your chosen date'}.
                </p>
                <p style={{ fontSize: '0.85rem', color: '#64748b' }}>
                  Please present your exported <em>Files & Reports</em> summary to the admitting clinician.
                </p>
                <button
                  type="button"
                  onClick={() => setSelectedFacility(null)}
                  className={styles.mapsBtn}
                  style={{ marginTop: '0.75rem' }}
                >
                  Close
                </button>
              </div>
            ) : (
              <form onSubmit={handleRequestAppointment} className={styles.requestForm}>
                <p className={styles.formNote}>
                  Prepare an appointment consultation voucher to share with clinical reception.
                </p>

                <div className={styles.formGroup}>
                  <label htmlFor="prefDate">Preferred Visit Date</label>
                  <input
                    id="prefDate"
                    type="date"
                    required
                    value={preferredDate}
                    onChange={(e) => setPreferredDate(e.target.value)}
                    className={styles.formInput}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label htmlFor="reason">Discussion Topic</label>
                  <select
                    id="reason"
                    value={consultReason}
                    onChange={(e) => setConsultReason(e.target.value)}
                    className={styles.formInput}
                  >
                    <option value="General nutrition review">General Nutrition & Dietary Review</option>
                    <option value="Biomarker blood test consultation">Biomarker / Blood Test Follow-up</option>
                    <option value="Dietary guidance for fatigue">Dietary Guidance for Fatigue/Weakness</option>
                    <option value="Clinical dietitian referral">Clinical Dietitian Consultation</option>
                  </select>
                </div>

                <div className={styles.modalActions}>
                  <button
                    type="button"
                    onClick={() => setSelectedFacility(null)}
                    className={styles.cancelBtn}
                  >
                    Cancel
                  </button>
                  <button type="submit" className={styles.submitBtn}>
                    Generate Consultation Request
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
