/**
 * Firebase Client Configuration pointing strictly to local Auth Emulator.
 *
 * Adheres to C-07, C-14, and GR-11:
 * - Uses local Auth Emulator at 127.0.0.1:9099
 * - Uses demo-mednourish project ID
 * - No cloud project or billing connection
 */

import { initializeApp } from 'firebase/app';
import {
  getAuth,
  connectAuthEmulator,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  User,
} from 'firebase/auth';

const firebaseConfig = {
  apiKey: 'fake-api-key-for-emulator',
  authDomain: 'demo-mednourish.firebaseapp.com',
  projectId: 'demo-mednourish',
  storageBucket: 'demo-mednourish.appspot.com',
  messagingSenderId: '000000000000',
  appId: '1:000000000000:web:0000000000000000000000',
};

// Initialize app with fictional configuration
export const app = initializeApp(firebaseConfig);

// Initialize Firebase Auth
export const auth = getAuth(app);

// Connect to local Auth Emulator
const authEmulatorHost = 'http://127.0.0.1:9099';
try {
  connectAuthEmulator(auth, authEmulatorHost, { disableWarnings: true });
} catch {
  // Ignored if already connected
}

export {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
};
export type { User };
