import React, { useState } from 'react';
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  auth,
} from '../services/firebase';
import { LogIn, UserPlus, AlertCircle } from 'lucide-react';
import styles from './AuthForm.module.css';

interface AuthFormProps {
  onSuccess: () => void;
}

export const AuthForm: React.FC<AuthFormProps> = ({ onSuccess }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setLoading(true);

    try {
      if (isRegister) {
        await createUserWithEmailAndPassword(auth, email.trim(), password);
      } else {
        await signInWithEmailAndPassword(auth, email.trim(), password);
      }
      onSuccess();
    } catch (err: unknown) {
      const error = err as { code?: string; message?: string };
      // Plain-language, non-revealing error messages per M1A.4 acceptance criteria
      if (error.code === 'auth/invalid-credential' || error.code === 'auth/wrong-password' || error.code === 'auth/user-not-found') {
        setErrorMsg('Invalid email or password. Please verify your credentials.');
      } else if (error.code === 'auth/email-already-in-use') {
        setErrorMsg('An account with this email already exists or is unavailable.');
      } else if (error.code === 'auth/weak-password') {
        setErrorMsg('Password should be at least 6 characters.');
      } else {
        setErrorMsg('Unable to complete request. Please ensure the Auth Emulator is running.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.authContainer}>
      <h2 className={styles.heading}>
        {isRegister ? 'Create Account' : 'Sign In to MedNourish'}
      </h2>

      {errorMsg && (
        <div className={styles.errorAlert} role="alert">
          <AlertCircle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.field}>
          <label htmlFor="auth-email" className={styles.label}>
            Email address
          </label>
          <input
            id="auth-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={styles.input}
            placeholder="fictional.user@example.com"
          />
        </div>

        <div className={styles.field}>
          <label htmlFor="auth-password" className={styles.label}>
            Password
          </label>
          <input
            id="auth-password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={styles.input}
            placeholder="••••••••"
          />
        </div>

        <button type="submit" disabled={loading} className={styles.submitBtn}>
          {isRegister ? <UserPlus size={18} /> : <LogIn size={18} />}
          {loading ? 'Processing...' : isRegister ? 'Register Account' : 'Sign In'}
        </button>
      </form>

      <div className={styles.switchMode}>
        <button
          type="button"
          onClick={() => {
            setIsRegister(!isRegister);
            setErrorMsg(null);
          }}
          className={styles.toggleBtn}
        >
          {isRegister
            ? 'Already have an account? Sign In'
            : "Don't have an account? Register"}
        </button>
      </div>
    </div>
  );
};
