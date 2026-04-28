import React, { useEffect, useState } from 'react';
import Login from './components/login/Login';
import { MainLayout } from './components/layout/MainLayout';
import { getCurrentUser, isAuthenticated, logout } from './services';
import './assets/styles/globals.css';

function App() {
  const [isAuthenticatedState, setIsAuthenticatedState] = useState<boolean>(() => isAuthenticated());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const verifySession = async () => {
      if (!isAuthenticated()) {
        setIsLoading(false);
        return;
      }

      try {
        await getCurrentUser();
        setIsAuthenticatedState(true);
      } catch {
        logout();
        setIsAuthenticatedState(false);
      } finally {
        setIsLoading(false);
      }
    };

    verifySession();
  }, []);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticatedState) {
    return <Login onLoginSuccess={() => setIsAuthenticatedState(true)} />;
  }

  return <MainLayout onLogout={() => {
    logout();
    setIsAuthenticatedState(false);
  }} />;
}

export default App;

