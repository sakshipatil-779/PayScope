"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import {
  signInWithPopup,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User as FirebaseUser,
} from "firebase/auth";
import { auth, googleProvider, isFirebaseConfigured } from "@/lib/firebase";

export interface AppUser {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
  isDemo?: boolean;
}

interface AuthContextType {
  user: AppUser | null;
  loading: boolean;
  isAuthModalOpen: boolean;
  openAuthModal: () => void;
  closeAuthModal: () => void;
  signInWithGoogle: () => Promise<void>;
  signInAsGuest: () => void;
  signOut: () => Promise<void>;
  isConfigured: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: false,
  isAuthModalOpen: false,
  openAuthModal: () => {},
  closeAuthModal: () => {},
  signInWithGoogle: async () => {},
  signInAsGuest: () => {},
  signOut: async () => {},
  isConfigured: false,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Initialize to null for SSR and initial hydration parity
  const [user, setUser] = useState<AppUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  useEffect(() => {
    // 1. Recover stored guest session asynchronously if present
    const timer = setTimeout(() => {
      try {
        const stored = localStorage.getItem("payscope_demo_user");
        if (stored) {
          setUser(JSON.parse(stored));
        }
      } catch {
        // Ignore
      }
      if (!isFirebaseConfigured || !auth) {
        setLoading(false);
      }
    }, 0);

    // 2. Listen to live Firebase authentication state
    if (isFirebaseConfigured && auth) {
      const unsubscribe = onAuthStateChanged(auth, (fbUser: FirebaseUser | null) => {
        if (fbUser) {
          setUser({
            uid: fbUser.uid,
            email: fbUser.email,
            displayName: fbUser.displayName,
            photoURL: fbUser.photoURL,
          });
          try {
            localStorage.removeItem("payscope_demo_user");
          } catch {
            // Ignore
          }
        } else {
          // If no Firebase user and no guest stored, reset to null
          try {
            const stored = localStorage.getItem("payscope_demo_user");
            if (!stored) {
              setUser(null);
            }
          } catch {
            setUser(null);
          }
        }
        setLoading(false);
      });
      return () => {
        clearTimeout(timer);
        unsubscribe();
      };
    }

    return () => {
      clearTimeout(timer);
    };
  }, []);

  const signInWithGoogle = async () => {
    setLoading(true);
    try {
      if (isFirebaseConfigured && auth && googleProvider) {
        const result = await signInWithPopup(auth, googleProvider);
        const fbUser = result.user;
        setUser({
          uid: fbUser.uid,
          email: fbUser.email,
          displayName: fbUser.displayName,
          photoURL: fbUser.photoURL,
        });
        setIsAuthModalOpen(false);
      } else {
        signInAsGuest();
      }
    } catch (err: unknown) {
      console.error("Google sign-in error:", err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const signInAsGuest = () => {
    const demoUser: AppUser = {
      uid: "guest-user-101",
      email: "guest@payscope.ai",
      displayName: "Demo User",
      photoURL: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80",
      isDemo: true,
    };
    setUser(demoUser);
    try {
      localStorage.setItem("payscope_demo_user", JSON.stringify(demoUser));
    } catch {
      // Ignore
    }
    setIsAuthModalOpen(false);
  };

  const signOut = async () => {
    setLoading(true);
    try {
      if (isFirebaseConfigured && auth) {
        await firebaseSignOut(auth);
      }
      try {
        localStorage.removeItem("payscope_demo_user");
      } catch {
        // Ignore
      }
      setUser(null);
    } catch (err) {
      console.error("Sign-out error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthModalOpen,
        openAuthModal: () => setIsAuthModalOpen(true),
        closeAuthModal: () => setIsAuthModalOpen(false),
        signInWithGoogle,
        signInAsGuest,
        signOut,
        isConfigured: isFirebaseConfigured,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
