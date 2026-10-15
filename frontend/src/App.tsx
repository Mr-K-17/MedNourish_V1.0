import React, { useEffect, useState, useRef } from 'react';
import {
  Activity,
  ShieldAlert,
  CheckCircle2,
  LogOut,
  Trash2,
  Edit3,
  ChevronDown,
  Sparkles,
  HeartPulse,
} from 'lucide-react';
import { onAuthStateChanged, signOut, auth, User as FirebaseUser } from './services/firebase';
import { DemoBanner } from './components/DemoBanner';
import { EmergencyHelpModal } from './components/EmergencyHelpModal';
import { AuthForm } from './components/AuthForm';
import { ConsentProfileModal } from './components/ConsentProfileModal';
import { Dashboard } from './components/Dashboard';
import { SymptomExplorer } from './components/SymptomExplorer';
import { ReportsView } from './components/ReportsView';
import { MedBotView } from './components/MedBotView';
import { CarePlanView } from './components/CarePlanView';
import { NurseBotView } from './components/NurseBotView';
import { MLLabView } from './components/MLLabView';
import { MedScanLiteView } from './components/MedScanLiteView';
import { VirtualWardView } from './components/VirtualWardView';
import styles from './App.module.css';

interface ServiceStatus {
  status?: string;
  message?: string;
  host?: string;
  database?: string;
  project?: string;
}

interface BackendHealth {
  status: string;
  version: string;
  environment: string;
  services?: {
    mysql?: ServiceStatus;
    mongodb?: ServiceStatus;
    firebase_auth_emulator?: ServiceStatus;
  };
}

interface UserProfileData {
  id: string;
  display_name?: string;
  gender?: string;
  height_cm?: number;
  weight_kg?: number;
  is_adult_confirmed: boolean;
  terms_consent_version: string;
  age?: number;
  blood_type?: string;
  conditions?: string[];
  other_condition?: string;
  under_18_notice?: string;
}

export const App: React.FC = () => {
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [currentUser, setCurrentUser] = useState<FirebaseUser | null>(null);
  const [idToken, setIdToken] = useState<string | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfileData | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [isEmergencyModalOpen, setIsEmergencyModalOpen] = useState(false);
  const [isEditProfileOpen, setIsEditProfileOpen] = useState(false);
  const [appError, setAppError] = useState<string | null>(null);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const [activeView, setActiveView] = useState<
    | 'dashboard'
    | 'symptom-explorer'
    | 'reports'
    | 'medbot'
    | 'careplan'
    | 'nursebot'
    | 'mllab'
    | 'medscan-lite'
    | 'virtual-ward'
  >('dashboard');

  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/v1/health')
      .then((res) => res.json())
      .then((data: BackendHealth) => setHealth(data))
      .catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setCurrentUser(user);
      if (user) {
        const token = await user.getIdToken();
        setIdToken(token);
        fetchUserProfile(token);
      } else {
        setIdToken(null);
        setUserProfile(null);
      }
    });
    return () => unsubscribe();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setProfileDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchUserProfile = async (token: string) => {
    setProfileLoading(true);
    setAppError(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/profile', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 200) {
        const data = await res.json();
        setUserProfile(data);
      } else if (res.status === 404) {
        setUserProfile(null);
      } else {
        setAppError('Unable to load user profile.');
      }
    } catch {
      setAppError('Backend service unreachable for profile sync.');
    } finally {
      setProfileLoading(false);
    }
  };

  const handleSignOut = async () => {
    setProfileDropdownOpen(false);
    await signOut(auth);
    setUserProfile(null);
    setIdToken(null);
  };

  const handleDeleteAccount = async () => {
    if (!idToken || !currentUser) return;
    setProfileDropdownOpen(false);
    const confirmed = window.confirm(
      'Are you sure you want to permanently delete your account and profile data? This action cannot be undone.'
    );
    if (!confirmed) return;

    try {
      await fetch('http://127.0.0.1:8000/v1/profile', {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${idToken}` },
      });
      await currentUser.delete();
      handleSignOut();
    } catch (err: unknown) {
      alert('Error deleting account: ' + (err as Error).message);
    }
  };

  const getInitials = (name?: string, email?: string | null) => {
    if (name && name.trim()) {
      const parts = name.trim().split(' ');
      if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
      return name.slice(0, 2).toUpperCase();
    }
    if (email) return email.slice(0, 2).toUpperCase();
    return 'MN';
  };

  return (
    <div className={styles.container}>
      <DemoBanner />

      <header className={styles.header}>
        <div
          className={styles.titleArea}
          onClick={() => setActiveView('dashboard')}
          title="Go to MedNourish Dashboard"
        >
          <div className={styles.logoBadge}>
            <Activity size={24} color="#ffffff" />
          </div>
          <div>
            <h1 className={styles.title}>MEDNOURISH</h1>
            <p className={styles.titleSub}>Precision Nutrition & Clinical Reference</p>
          </div>
        </div>

        <div className={styles.headerActions}>
          {health && (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                fontSize: '0.78rem',
                color: 'rgba(255, 255, 255, 0.9)',
                background: 'rgba(255, 255, 255, 0.15)',
                padding: '0.3rem 0.75rem',
                borderRadius: '20px',
                border: '1px solid rgba(255, 255, 255, 0.25)',
              }}
            >
              <CheckCircle2 size={13} color="#a7f3d0" />
              <span>System Online</span>
            </div>
          )}

          <button
            type="button"
            onClick={() => setIsEmergencyModalOpen(true)}
            className={styles.urgentHelpButton}
          >
            <ShieldAlert size={17} />
            <span>Need Urgent Help?</span>
          </button>

          {/* Profile on Top Right with Edit Features */}
          {currentUser && (
            <div style={{ position: 'relative' }} ref={dropdownRef}>
              <button
                type="button"
                className={styles.profileBtn}
                onClick={() => setProfileDropdownOpen((prev) => !prev)}
                aria-expanded={profileDropdownOpen}
                aria-label="Profile navigation menu"
              >
                <div className={styles.profileAvatar}>
                  {getInitials(userProfile?.display_name, currentUser.email)}
                </div>
                <span
                  style={{
                    maxWidth: '120px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {userProfile?.display_name || currentUser.email?.split('@')[0]}
                </span>
                <ChevronDown size={14} style={{ opacity: 0.8 }} />
              </button>

              {profileDropdownOpen && (
                <div className={styles.profileDropdown}>
                  <div className={styles.dropdownHeader}>
                    <p className={styles.dropdownName}>
                      {userProfile?.display_name || 'Registered Member'}
                    </p>
                    <p className={styles.dropdownEmail}>{currentUser.email}</p>
                    {userProfile && (
                      <div
                        style={{
                          marginTop: '6px',
                          display: 'flex',
                          flexWrap: 'wrap',
                          gap: '4px',
                          fontSize: '0.74rem',
                        }}
                      >
                        {userProfile.age && (
                          <span
                            style={{
                              background: '#e0f2fe',
                              color: '#0369a1',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              fontWeight: 600,
                            }}
                          >
                            Age {userProfile.age}
                          </span>
                        )}
                        {userProfile.blood_type && (
                          <span
                            style={{
                              background: '#fef3c7',
                              color: '#92400e',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              fontWeight: 600,
                            }}
                          >
                            Blood {userProfile.blood_type}
                          </span>
                        )}
                        <span
                          style={{
                            background: '#dcfce7',
                            color: '#15803d',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontWeight: 600,
                          }}
                        >
                          {userProfile.is_adult_confirmed ? 'Adult 18+' : 'Consent Active'}
                        </span>
                      </div>
                    )}
                  </div>

                  {userProfile?.conditions && userProfile.conditions.length > 0 && (
                    <div style={{ padding: '0.6rem 1rem', background: '#f8fafc' }}>
                      <p
                        style={{
                          margin: 0,
                          fontSize: '0.72rem',
                          color: 'var(--color-text-muted)',
                          fontWeight: 700,
                          textTransform: 'uppercase',
                        }}
                      >
                        Active Health Profile
                      </p>
                      <p
                        style={{
                          margin: '3px 0 0 0',
                          fontSize: '0.8rem',
                          color: 'var(--color-text-secondary)',
                        }}
                      >
                        {userProfile.conditions.join(', ')}
                      </p>
                    </div>
                  )}

                  <button
                    type="button"
                    className={styles.dropdownItem}
                    onClick={() => {
                      setIsEditProfileOpen(true);
                      setProfileDropdownOpen(false);
                    }}
                  >
                    <Edit3 size={15} color="var(--color-primary)" />
                    <span>Edit Profile Details</span>
                  </button>

                  <hr className={styles.dropdownDivider} />

                  <button
                    type="button"
                    className={styles.dropdownItem}
                    onClick={handleSignOut}
                  >
                    <LogOut size={15} />
                    <span>Sign Out</span>
                  </button>

                  <button
                    type="button"
                    className={`${styles.dropdownItem} ${styles.dropdownItemDanger}`}
                    onClick={handleDeleteAccount}
                  >
                    <Trash2 size={15} />
                    <span>Delete Account & Data</span>
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      <main className={styles.main}>
        {appError && (
          <div
            style={{
              padding: '0.75rem 1rem',
              background: '#fee2e2',
              border: '1px solid #fca5a5',
              borderRadius: '8px',
              color: '#b91c1c',
              marginBottom: '1rem',
            }}
          >
            {appError}
          </div>
        )}

        {!currentUser ? (
          <AuthForm onSuccess={() => {}} />
        ) : profileLoading ? (
          <div
            style={{
              textAlign: 'center',
              padding: '4rem',
              color: 'var(--color-text-secondary)',
            }}
          >
            <HeartPulse
              size={36}
              style={{
                color: 'var(--color-primary)',
                animation: 'pulse 1.5s infinite',
                margin: '0 auto 1rem auto',
                display: 'block',
              }}
            />
            Loading user profile...
          </div>
        ) : !userProfile ? (
          idToken && (
            <ConsentProfileModal
              idToken={idToken}
              onProfileCreated={() => fetchUserProfile(idToken)}
            />
          )
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {activeView === 'symptom-explorer' && idToken ? (
              <SymptomExplorer
                idToken={idToken}
                onBackToDashboard={() => setActiveView('dashboard')}
              />
            ) : activeView === 'reports' && idToken ? (
              <ReportsView
                idToken={idToken}
                onBackToDashboard={() => setActiveView('dashboard')}
              />
            ) : activeView === 'medbot' && idToken ? (
              <MedBotView
                idToken={idToken}
                onBackToDashboard={() => setActiveView('dashboard')}
              />
            ) : activeView === 'careplan' && idToken ? (
              <CarePlanView
                idToken={idToken}
                onBackToDashboard={() => setActiveView('dashboard')}
              />
            ) : activeView === 'nursebot' && idToken ? (
              <NurseBotView
                idToken={idToken}
                onBackToDashboard={() => setActiveView('dashboard')}
                onOpenEmergencyModal={() => setIsEmergencyModalOpen(true)}
                onNavigateToView={(view) => setActiveView(view)}
              />
            ) : activeView === 'mllab' && idToken ? (
              <MLLabView
                idToken={idToken}
                onBackToDashboard={() => setActiveView('dashboard')}
                onOpenEmergencyModal={() => setIsEmergencyModalOpen(true)}
              />
            ) : activeView === 'medscan-lite' ? (
              <MedScanLiteView
                idToken={idToken}
                onBackToDashboard={() => setActiveView('dashboard')}
                onOpenEmergencyModal={() => setIsEmergencyModalOpen(true)}
                onHandoffToExplorer={() => setActiveView('symptom-explorer')}
              />
            ) : activeView === 'virtual-ward' ? (
              <VirtualWardView
                idToken={idToken}
                onBackToDashboard={() => setActiveView('dashboard')}
                onOpenEmergencyModal={() => setIsEmergencyModalOpen(true)}
              />
            ) : (
              <Dashboard
                displayName={userProfile.display_name}
                consentVersion={userProfile.terms_consent_version}
                onSelectTile={(tileId) => {
                  if (tileId === 'symptom-explorer') setActiveView('symptom-explorer');
                  else if (tileId === 'reports') setActiveView('reports');
                  else if (tileId === 'medbot') setActiveView('medbot');
                  else if (tileId === 'careplan') setActiveView('careplan');
                  else if (tileId === 'nursebot') setActiveView('nursebot');
                  else if (tileId === 'mllab') setActiveView('mllab');
                  else if (tileId === 'medscan-lite') setActiveView('medscan-lite');
                  else if (tileId === 'virtual-ward') setActiveView('virtual-ward');
                }}
              />
            )}
          </div>
        )}
      </main>

      {/* Floating Corner Icon for Experimental ML Lab */}
      {currentUser && userProfile && activeView !== 'mllab' && (
        <button
          type="button"
          onClick={() => setActiveView('mllab')}
          title="Experimental ML Lab (not for health decisions)"
          style={{
            position: 'fixed',
            bottom: '1.75rem',
            right: '1.75rem',
            width: '54px',
            height: '54px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #0d7377, #10b981)',
            border: '2px solid rgba(255, 255, 255, 0.8)',
            boxShadow: '0 8px 24px rgba(13, 115, 119, 0.45)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 90,
            transition: 'all 0.25s ease',
            color: '#ffffff',
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.transform = 'scale(1.1) translateY(-2px)';
            (e.currentTarget as HTMLButtonElement).style.boxShadow =
              '0 12px 28px rgba(13, 115, 119, 0.6)';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.transform = 'scale(1)';
            (e.currentTarget as HTMLButtonElement).style.boxShadow =
              '0 8px 24px rgba(13, 115, 119, 0.45)';
          }}
        >
          <Sparkles size={24} />
        </button>
      )}

      {/* Profile Edit Modal Dialog */}
      {isEditProfileOpen && idToken && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.55)',
            backdropFilter: 'blur(3px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
            overflowY: 'auto',
          }}
          onClick={() => setIsEditProfileOpen(false)}
        >
          <div
            style={{ width: '100%', maxWidth: '640px', maxHeight: '90vh', overflowY: 'auto' }}
            onClick={(e) => e.stopPropagation()}
          >
            <ConsentProfileModal
              idToken={idToken}
              existingProfile={userProfile}
              onProfileCreated={() => {
                fetchUserProfile(idToken);
                setIsEditProfileOpen(false);
              }}
              onClose={() => setIsEditProfileOpen(false)}
            />
          </div>
        </div>
      )}

      <EmergencyHelpModal
        isOpen={isEmergencyModalOpen}
        onClose={() => setIsEmergencyModalOpen(false)}
      />

      <footer className={styles.footer}>
        MEDNOURISH Precision Health · Educational Reference Prototype · Not for clinical diagnosis or emergency triage
      </footer>
    </div>
  );
};

export default App;
