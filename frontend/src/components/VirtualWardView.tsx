import React, { useState } from 'react';
import {
  Building2,
  ArrowLeft,
  Navigation,
  AlertTriangle,
  Calendar,
  ExternalLink,
  MapPin,
  Map as MapIcon,
  List,
  Search,
} from 'lucide-react';
import styles from './VirtualWardView.module.css';

interface Facility {
  id: string;
  name: string;
  type: 'General Hospital' | 'Community Health Center' | 'Emergency Care';
  categoryDescription: string;
  mapsQuery: string;
  latitude: number;
  longitude: number;
  address: string;
  phone: string;
}

const LOCAL_FACILITIES: Facility[] = [
  {
    id: 'fac-1',
    name: 'Metropolitan General & Multi-Specialty Hospital',
    type: 'General Hospital',
    categoryDescription: 'Comprehensive outpatient and inpatient medical services, nutrition panels, and pathology labs.',
    mapsQuery: 'General+Hospital+near+me',
    latitude: 19.0760,
    longitude: 72.8777,
    address: 'Central Healthcare Corridor, Main Avenue',
    phone: '+91 (022) 2410-8000',
  },
  {
    id: 'fac-2',
    name: 'Community Primary Health & Nutrition Center (CHC)',
    type: 'Community Health Center',
    categoryDescription: 'Public primary health clinics, nutrition counseling, preventive care, and maternal/child wellness.',
    mapsQuery: 'Community+Health+Center+near+me',
    latitude: 19.0850,
    longitude: 72.8890,
    address: 'East Civic Sector 4, Community Road',
    phone: '+91 (022) 2522-1100',
  },
  {
    id: 'fac-3',
    name: 'Apex Trauma Center & 24/7 Emergency Ward',
    type: 'Emergency Care',
    categoryDescription: '24/7 acute trauma and emergency medical interventions, critical care, and ambulance dispatch.',
    mapsQuery: 'Emergency+Hospital+near+me',
    latitude: 19.0680,
    longitude: 72.8650,
    address: 'Expressway Junction, Sector 12',
    phone: 'Emergency: 112 / 108',
  },
  {
    id: 'fac-4',
    name: 'District Clinical Diagnostics & Endocrinology Wing',
    type: 'General Hospital',
    categoryDescription: 'Specialized micronutrient testing, vitamin biomarker panels, endocrine and metabolic assessments.',
    mapsQuery: 'Diagnostic+Center+near+me',
    latitude: 19.0920,
    longitude: 72.8620,
    address: 'Medical Research Enclave, Park Road',
    phone: '+91 (022) 2650-4433',
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
  const [activeFacility, setActiveFacility] = useState<Facility>(LOCAL_FACILITIES[0]);
  const [viewMode, setViewMode] = useState<'both' | 'map' | 'list'>('both');
  const [searchFilter, setSearchFilter] = useState('');
  const [appointmentRequested, setAppointmentRequested] = useState<boolean>(false);
  const [reminderCreated, setReminderCreated] = useState<boolean>(false);
  const [preferredDate, setPreferredDate] = useState<string>('');
  const [consultReason, setConsultReason] = useState<string>('General nutrition review');

  const filteredFacilities = LOCAL_FACILITIES.filter(
    (f) =>
      f.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
      f.type.toLowerCase().includes(searchFilter.toLowerCase()) ||
      f.categoryDescription.toLowerCase().includes(searchFilter.toLowerCase())
  );

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

  // Generate OpenStreetMap embed URL around active facility
  const mapBbox = `${activeFacility.longitude - 0.04},${activeFacility.latitude - 0.03},${activeFacility.longitude + 0.04},${activeFacility.latitude + 0.03}`;
  const mapUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${mapBbox}&layer=mapnik&marker=${activeFacility.latitude},${activeFacility.longitude}`;

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
          <h2 className={styles.title}>VirtualWard Facility Directory & Live Map</h2>
        </div>
      </div>

      {/* Safety Notice */}
      <div className={styles.warningBanner}>
        <AlertTriangle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
        <div>
          <strong>Educational Prototype Notice:</strong> MedNourish does NOT
          provide autonomous medical triage or live booking with hospital EMR systems. If you have
          acute symptoms, chest pain, breathing difficulty, or severe weakness, contact emergency
          services immediately.
          <div style={{ marginTop: '0.4rem' }}>
            <button
              type="button"
              onClick={onOpenEmergencyModal}
              className={styles.emergencyLinkBtn}
            >
              Open Urgent Help & Emergency Contacts →
            </button>
          </div>
        </div>
      </div>

      {/* Search and View Controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          background: 'var(--color-bg-surface)',
          padding: '0.85rem 1.25rem',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: '1', minWidth: '260px' }}>
          <Search size={18} color="var(--color-text-muted)" />
          <input
            type="text"
            placeholder="Search hospitals, CHCs, trauma centers, diagnostics..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            style={{
              width: '100%',
              border: 'none',
              outline: 'none',
              fontSize: '0.9rem',
              color: 'var(--color-text-primary)',
              fontFamily: 'inherit',
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '0.4rem' }}>
          <button
            type="button"
            onClick={() => setViewMode('both')}
            style={{
              padding: '0.4rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid var(--color-border)',
              background: viewMode === 'both' ? 'var(--color-primary)' : 'var(--color-bg-app)',
              color: viewMode === 'both' ? '#ffffff' : 'var(--color-text-secondary)',
              cursor: 'pointer',
              fontSize: '0.82rem',
              fontWeight: 600,
            }}
          >
            Split View
          </button>
          <button
            type="button"
            onClick={() => setViewMode('map')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.4rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid var(--color-border)',
              background: viewMode === 'map' ? 'var(--color-primary)' : 'var(--color-bg-app)',
              color: viewMode === 'map' ? '#ffffff' : 'var(--color-text-secondary)',
              cursor: 'pointer',
              fontSize: '0.82rem',
              fontWeight: 600,
            }}
          >
            <MapIcon size={14} /> Map Only
          </button>
          <button
            type="button"
            onClick={() => setViewMode('list')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.4rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid var(--color-border)',
              background: viewMode === 'list' ? 'var(--color-primary)' : 'var(--color-bg-app)',
              color: viewMode === 'list' ? '#ffffff' : 'var(--color-text-secondary)',
              cursor: 'pointer',
              fontSize: '0.82rem',
              fontWeight: 600,
            }}
          >
            <List size={14} /> List Only
          </button>
        </div>
      </div>

      {/* Main Content Area (Map + List) */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns:
            viewMode === 'both'
              ? 'repeat(auto-fit, minmax(420px, 1fr))'
              : '1fr',
          gap: '1.5rem',
          alignItems: 'start',
        }}
      >
        {/* Interactive Map Component */}
        {(viewMode === 'both' || viewMode === 'map') && (
          <div
            style={{
              background: 'var(--color-bg-surface)',
              borderRadius: 'var(--radius-xl)',
              overflow: 'hidden',
              border: '1px solid var(--color-border)',
              boxShadow: 'var(--shadow-md)',
              position: 'sticky',
              top: '5.5rem',
            }}
          >
            <div
              style={{
                background: 'var(--grad-header)',
                padding: '0.85rem 1.25rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                color: '#ffffff',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <MapPin size={18} />
                <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>
                  {activeFacility.name}
                </span>
              </div>
              <span style={{ fontSize: '0.75rem', opacity: 0.9 }}>
                Interactive Facility Radar
              </span>
            </div>

            <div style={{ position: 'relative', height: '420px', width: '100%', background: '#e2e8f0' }}>
              <iframe
                title="VirtualWard Hospital Map"
                src={mapUrl}
                style={{
                  width: '100%',
                  height: '100%',
                  border: 'none',
                }}
                loading="lazy"
                sandbox="allow-scripts allow-same-origin"
              />
            </div>

            <div
              style={{
                padding: '0.85rem 1.25rem',
                background: '#f8fafc',
                borderTop: '1px solid var(--color-border)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '0.5rem',
              }}
            >
              <div>
                <p style={{ margin: 0, fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  {activeFacility.address}
                </p>
                <p style={{ margin: '2px 0 0 0', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                  Phone: {activeFacility.phone}
                </p>
              </div>
              <button
                type="button"
                onClick={() => handleOpenMaps(activeFacility.mapsQuery)}
                className={styles.mapsBtn}
                style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}
              >
                <Navigation size={13} /> Open Live GPS Directions <ExternalLink size={11} />
              </button>
            </div>
          </div>
        )}

        {/* Facilities List */}
        {(viewMode === 'both' || viewMode === 'list') && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {filteredFacilities.map((fac) => {
              const isSelected = activeFacility.id === fac.id;
              return (
                <div
                  key={fac.id}
                  className={styles.facilityCard}
                  style={{
                    border: isSelected
                      ? '2px solid var(--color-primary)'
                      : '1px solid var(--color-border)',
                    boxShadow: isSelected ? 'var(--shadow-md)' : 'var(--shadow-sm)',
                    background: isSelected ? '#fafffd' : 'var(--color-bg-surface)',
                  }}
                  onClick={() => setActiveFacility(fac)}
                >
                  <div className={styles.facilityHeader}>
                    <span className={styles.facilityBadge}>{fac.type}</span>
                    {isSelected && (
                      <span
                        style={{
                          fontSize: '0.72rem',
                          color: 'var(--color-primary-dark)',
                          background: 'var(--color-primary-light)',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontWeight: 700,
                        }}
                      >
                        Pinned on Map
                      </span>
                    )}
                  </div>

                  <h3 className={styles.facilityName}>{fac.name}</h3>
                  <p className={styles.facilityAddress}>{fac.categoryDescription}</p>

                  <div
                    style={{
                      margin: '0.5rem 0',
                      fontSize: '0.8rem',
                      color: 'var(--color-text-secondary)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                    }}
                  >
                    <MapPin size={14} color="var(--color-primary)" />
                    <span>{fac.address}</span>
                  </div>

                  <div className={styles.cardActions}>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveFacility(fac);
                      }}
                      className={styles.mapsBtn}
                      style={{ background: '#f1f5f9', color: 'var(--color-text-primary)' }}
                    >
                      <MapIcon size={14} /> Center on Map
                    </button>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenMaps(fac.mapsQuery);
                      }}
                      className={styles.mapsBtn}
                      title="Search nearby facilities via Google Maps"
                    >
                      <Navigation size={14} /> Navigation <ExternalLink size={12} />
                    </button>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedFacility(fac);
                        setAppointmentRequested(false);
                      }}
                      className={styles.consultBtn}
                    >
                      <Calendar size={14} /> Consultation Sheet
                    </button>
                  </div>
                </div>
              );
            })}

            {/* Quick CarePlan Add */}
            <div
              className={styles.facilityCard}
              style={{ background: '#f8fafc', borderStyle: 'dashed' }}
            >
              <div className={styles.facilityHeader}>
                <span
                  className={styles.facilityBadge}
                  style={{
                    background: '#e2e8f0',
                    color: '#475569',
                    borderColor: '#cbd5e1',
                  }}
                >
                  Preventive Care Sync
                </span>
              </div>
              <h3 className={styles.facilityName}>Schedule Routine Primary Check-up</h3>
              <p className={styles.facilityAddress}>
                Add an automated reminder to your personal CarePlan daily wellness checklist to schedule annual or bi-annual check-ups with your physician.
              </p>
              <div className={styles.cardActions}>
                <button
                  type="button"
                  onClick={handleAddCheckupReminder}
                  disabled={reminderCreated}
                  className={styles.mapsBtn}
                >
                  <Calendar size={14} />{' '}
                  {reminderCreated ? 'Check-up Task Added!' : 'Add Check-up Task to CarePlan'}
                </button>
              </div>
            </div>
          </div>
        )}
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
                <h4>Consultation Sheet Prepared</h4>
                <p>
                  Your consultation request record has been formatted for your upcoming visit to{' '}
                  <strong>{selectedFacility.name}</strong> on {preferredDate || 'your selected date'}.
                </p>
                <p style={{ fontSize: '0.85rem', color: '#64748b' }}>
                  Please present your exported <em>Files & Reports</em> nutritional summary to the attending physician.
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
