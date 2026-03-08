import React, { useState } from 'react';
import Login from './components/login/Login';
import { MainLayout } from './components/layout/MainLayout';
import './assets/styles/globals.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  if (!isAuthenticated) {
    return <Login onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  return <MainLayout />;
}

export default App;

