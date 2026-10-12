import React, { useEffect, useState } from 'react';
import { Activity, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { DemoBanner } from './components/DemoBanner';
import styles from './App.module.css';

interface BackendHealth {
  status: string;
  version: string;
  environment: string;
}

export const App: React.FC = () => {
  const [health, setHealth] = useState<BackendHealth | null>(null);

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
        <a href="#urgent-help" className={styles.urgentHelpButton} role="button">
          <ShieldAlert size={18} />
          Need urgent help?
        </a>
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
        </section>
      </main>

      <footer className={styles.footer}>
        MEDNOURISH Phase 1A MVP Prototype · Strictly Local Development · Fictional Data Only
      </footer>
    </div>
  );
};

export default App;
