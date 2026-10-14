import React, { useState } from 'react';
import {
  Building2,
  ArrowLeft,
  MapPin,
  Phone,
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
  address: string;
  city: string;
  phone: string;
  mapsQuery: string;
  distanceNote: string;
}

const LOCAL_FACILITIES: Facility[] = [
  {
    id: 'fac-1',
    name: 'District General Hospital',
    type: 'General Hospital',
    address: 'Civil Lines Road, Near Medical College',
    city: 'Local Healthcare Zone',
    phone: '102 / Local Hospital Line',
    mapsQuery: 'General+Hospital+near+me',
    distanceNote: 'Primary Public Hospital · 24/7 Casualty',
  },
  {
    id: 'fac-2',
    name: 'City Community Health Center (CHC)',
    type: 'Community Health Center',
    address: 'Sector 4, Main Public Health Complex',
    city: 'Local Healthcare Zone',
    phone: 'Local Public Health Office',
    mapsQuery: 'Community+Health+Center+near+me',
    distanceNote: 'Outpatient Consultations & Nutrition Counseling',
  },
  {
    id: 'fac-3',
    name: 'Metropolitan Emergency Care & Trauma Unit',
    type: 'Emergency Care',
    address: 'Ring Road Bypass',
    city: 'Local Healthcare Zone',
    phone: '112 / 108 Emergency Medical Services',
    mapsQuery: 'Emergency+Hospital+near+me',
    distanceNote: 'Dedicated Acute Emergency Service',
  },
];

interface VirtualWardViewProps {
  onBackToDashboard: () => void;
  onOpenEmergencyModal: () => void;
}

export const VirtualWardView: React.FC<VirtualWardViewProps> = ({
  onBackToDashboard,
  onOpenEmergencyModal,
}) => {
  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(null);
  const [appointmentRequested, setAppointmentRequested] = useState<boolean>(false);
  const [preferredDate, setPreferredDate] = useState<string>('');
  const [consultReason, setConsultReason] = useState<string>('General nutrition review');

  const handleOpenMaps = (query: string) => {
    const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
    window.open(url, '_blank', 'noopener,noreferrer');
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
              <span className={styles.distanceBadge}>{fac.distanceNote}</span>
            </div>

            <h3 className={styles.facilityName}>{fac.name}</h3>
            <p className={styles.facilityAddress}>
              <MapPin size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
              {fac.address}, {fac.city}
            </p>
            <p className={styles.facilityPhone}>
              <Phone size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
              Phone: {fac.phone}
            </p>

            <div className={styles.cardActions}>
              <button
                type="button"
                onClick={() => handleOpenMaps(fac.mapsQuery)}
                className={styles.mapsBtn}
                title="Open location search in Google Maps"
              >
                <Navigation size={14} /> Open in Google Maps <ExternalLink size={12} />
              </button>

              <button
                type="button"
                onClick={() => {
                  setSelectedFacility(fac);
                  setAppointmentRequested(false);
                }}
                className={styles.consultBtn}
              >
                <Calendar size={14} /> Request Consultation
              </button>
            </div>
          </div>
        ))}
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
