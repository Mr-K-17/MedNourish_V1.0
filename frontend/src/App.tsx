import React, { useEffect, useState } from 'react';
import { Activity, ShieldAlert, CheckCircle2, User, LogOut, Trash2 } from 'lucide-react';
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
}

export const App: React.FC = () => {
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [currentUser, setCurrentUser] = useState<FirebaseUser | null>(null);
  const [idToken, setIdToken] = useState<string | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfileData | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [isEmergencyModalOpen, setIsEmergencyModalOpen] = useState(false);
  const [appError, setAppError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'dashboard' | 'symptom-explorer' | 'reports' | 'medbot' | 'careplan' | 'nursebot' | 'mllab' | 'medscan-lite' | 'virtual-ward'>('dashboard');

  useEffect(() => {
    // Probe local backend health endpoint
    fetch('http://127.0.0.1:8000/v1/health')
      .then((res) => res.json())
      .then((data: BackendHealth) => setHealth(data))
      .catch(() => {
        setHealth(null);
      });
  }, []);

  useEffect(() => {
    // Listen for auth state changes on emulator
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
        // Needs initial consent & profile setup
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
    await signOut(auth);
    setUserProfile(null);
    setIdToken(null);
  };

  const handleDeleteAccount = async () => {
    if (!idToken || !currentUser) return;
    const confirmed = window.confirm(
      'Are you sure you want to permanently delete your account and profile data? This action cannot be undone.'
    );
    if (!confirmed) return;

    try {
      // 1. Delete database profile & consent logs
      await fetch('http://127.0.0.1:8000/v1/profile', {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${idToken}` },
      });
      // 2. Delete user on Auth Emulator
      await currentUser.delete();
      handleSignOut();
    } catch (err: unknown) {
      alert('Error deleting account: ' + (err as Error).message);
    }
  };

  return (
    <div className={styles.container}>
      <DemoBanner />

      <header className={styles.header}>
        <div className={styles.titleArea}>
          <Activity size={28} color="var(--color-primary)" />
          <h1 className={styles.title}>MEDNOURISH</h1>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {currentUser && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
              <User size={16} />
              <span>{userProfile?.display_name || currentUser.email}</span>
              <button
                type="button"
                onClick={handleSignOut}
                className={styles.signOutButton}
                title="Sign Out"
              >
                <LogOut size={16} />
                Sign Out
              </button>
            </div>
          )}

          {/* Emergency safety layer reachable from every screen per C-20 & SAF-03 */}
          <button
            type="button"
            onClick={() => setIsEmergencyModalOpen(true)}
            className={styles.urgentHelpButton}
          >
            <ShieldAlert size={18} />
            Need urgent help?
          </button>
        </div>
      </header>

      <main className={styles.main}>
        {/* System & Services Dashboard Card */}
        <section className={styles.card} style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
            <h2 className={styles.cardTitle} style={{ margin: 0 }}>
              Phase 1A Prototype Environment
            </h2>
            <div className={styles.statusIndicator}>
              <CheckCircle2 size={18} />
              <span>
                Backend:{' '}
                {health ? `${health.status} (${health.environment})` : 'Offline / Mock mode'}
              </span>
            </div>
          </div>

          {health?.services && (
            <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.85rem', padding: '0.25rem 0.5rem', background: '#f1f5f9', borderRadius: '4px', border: '1px solid #cbd5e1' }}>
                <strong>MySQL (Users/Consent):</strong> {health.services.mysql?.status || 'unknown'}
              </span>
              <span style={{ fontSize: '0.85rem', padding: '0.25rem 0.5rem', background: '#f1f5f9', borderRadius: '4px', border: '1px solid #cbd5e1' }}>
                <strong>MongoDB (Reference Knowledge):</strong> {health.services.mongodb?.status || 'unknown'}
              </span>
              <span style={{ fontSize: '0.85rem', padding: '0.25rem 0.5rem', background: '#f1f5f9', borderRadius: '4px', border: '1px solid #cbd5e1' }}>
                <strong>Firebase Auth Emulator:</strong> {health.services.firebase_auth_emulator?.host || '127.0.0.1:9099'}
              </span>
            </div>
          )}
        </section>

        {appError && (
          <div style={{ padding: '0.75rem 1rem', background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: '8px', color: '#b91c1c', marginBottom: '1rem' }}>
            {appError}
          </div>
        )}

        {/* Auth / Profile Workflow State */}
        {!currentUser ? (
          <AuthForm onSuccess={() => {}} />
        ) : profileLoading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--color-text-secondary)' }}>
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
                  if (tileId === 'symptom-explorer') {
                    setActiveView('symptom-explorer');
                  } else if (tileId === 'reports') {
                    setActiveView('reports');
                  } else if (tileId === 'medbot') {
                    setActiveView('medbot');
                  } else if (tileId === 'careplan') {
                    setActiveView('careplan');
                  } else if (tileId === 'nursebot') {
                    setActiveView('nursebot');
                  } else if (tileId === 'mllab') {
                    setActiveView('mllab');
                  } else if (tileId === 'medscan-lite') {
                    setActiveView('medscan-lite');
                  } else if (tileId === 'virtual-ward') {
                    setActiveView('virtual-ward');
                  }
                }}
              />
            )}

            <section className={styles.card}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                  <h3 className={styles.cardTitle} style={{ margin: 0, fontSize: '1.1rem' }}>Account & Profile Summary</h3>
                  <p style={{ margin: '0.25rem 0 1rem 0', color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                    User ID: {currentUser.uid} · Email: {currentUser.email}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleDeleteAccount}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.5rem 0.75rem',
                    background: '#fff1f2',
                    border: '1px solid #fda4af',
                    color: '#e11d48',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                  }}
                >
                  <Trash2 size={16} /> Delete Account & Data
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '0.5rem' }}>
                <div style={{ padding: '0.75rem 1rem', background: 'var(--color-bg-app)', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Adult Confirmation</span>
                  <p style={{ margin: '0.25rem 0 0 0', fontWeight: 600, color: 'var(--color-accent)' }}>18+ Confirmed (SAF-10)</p>
                </div>

                <div style={{ padding: '0.75rem 1rem', background: 'var(--color-bg-app)', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Gender</span>
                  <p style={{ margin: '0.25rem 0 0 0', fontWeight: 500 }}>{userProfile.gender || 'Not specified'}</p>
                </div>

                <div style={{ padding: '0.75rem 1rem', background: 'var(--color-bg-app)', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Height</span>
                  <p style={{ margin: '0.25rem 0 0 0', fontWeight: 500 }}>{userProfile.height_cm ? `${userProfile.height_cm} cm` : 'Not specified'}</p>
                </div>

                <div style={{ padding: '0.75rem 1rem', background: 'var(--color-bg-app)', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Weight</span>
                  <p style={{ margin: '0.25rem 0 0 0', fontWeight: 500 }}>{userProfile.weight_kg ? `${userProfile.weight_kg} kg` : 'Not specified'}</p>
                </div>
              </div>
            </section>
          </div>
        )}
      </main>

      <EmergencyHelpModal
        isOpen={isEmergencyModalOpen}
        onClose={() => setIsEmergencyModalOpen(false)}
      />

      <footer className={styles.footer}>
        MEDNOURISH Phase 1A MVP Prototype · Strictly Local Development · Fictional Data Only
      </footer>
    </div>
  );
};

export default App;
