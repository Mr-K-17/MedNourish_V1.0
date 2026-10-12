import React, { useEffect, useState } from 'react';
import { Activity, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { DemoBanner } from './components/DemoBanner';
import { EmergencyHelpModal } from './components/EmergencyHelpModal';
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

export const App: React.FC = () => {
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [isEmergencyModalOpen, setIsEmergencyModalOpen] = useState(false);

  useEffect(() => {
    // Probe local backend health endpoint
    fetch('http://127.0.0.1:8000/v1/health')
      .then((res) => res.json())
      .then((data: BackendHealth) => setHealth(data))
      .catch(() => {
        // Expected when backend is not actively running during static compilation
        setHealth(null);
      });
  }, []);

  return (
    <div className={styles.container}>
      <DemoBanner />

      <header className={styles.header}>
        <div className={styles.titleArea}>
          <Activity size={28} color="var(--color-primary)" />
          <h1 className={styles.title}>MEDNOURISH</h1>
        </div>

        {/* Emergency safety layer reachable from every screen per C-20 & SAF-03 */}
        <button
          type="button"
          onClick={() => setIsEmergencyModalOpen(true)}
          className={styles.urgentHelpButton}
        >
          <ShieldAlert size={18} />
          Need urgent help?
        </button>
      </header>

      <main className={styles.main}>
        <section className={styles.card}>
          <h2 className={styles.cardTitle}>Phase 1A Development Scaffold</h2>
          <p>
            Welcome to the MEDNOURISH development environment. Phase 1A provides the safe local
            scaffold for adult (18+) nutritional deficiency reference matching.
          </p>

          <div className={styles.statusIndicator}>
            <CheckCircle2 size={18} />
            <span>
              Backend status:{' '}
              {health ? `${health.status} (${health.environment})` : 'Offline / Mock mode'}
            </span>
          </div>

          {health?.services && (
            <div style={{ marginTop: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.85rem', padding: '0.25rem 0.5rem', background: '#f1f5f9', borderRadius: '4px', border: '1px solid #cbd5e1' }}>
                <strong>MySQL:</strong> {health.services.mysql?.status || 'unknown'}
              </span>
              <span style={{ fontSize: '0.85rem', padding: '0.25rem 0.5rem', background: '#f1f5f9', borderRadius: '4px', border: '1px solid #cbd5e1' }}>
                <strong>MongoDB:</strong> {health.services.mongodb?.status || 'unknown'}
              </span>
              <span style={{ fontSize: '0.85rem', padding: '0.25rem 0.5rem', background: '#f1f5f9', borderRadius: '4px', border: '1px solid #cbd5e1' }}>
                <strong>Auth Emulator:</strong> {health.services.firebase_auth_emulator?.host || '127.0.0.1:9099'}
              </span>
            </div>
          )}
        </section>
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
