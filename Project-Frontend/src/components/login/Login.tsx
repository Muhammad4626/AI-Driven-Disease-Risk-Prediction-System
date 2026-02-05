import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './Login.module.css';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle login logic here
    console.log('Login attempt:', { email, password });
    
    // TODO: Add actual authentication logic here
    // For now, redirect to dashboard on any login attempt
    navigate('/dashboard');
  };

  return (
    <div className={styles.loginContainer}>
      {/* Left Section - Project Information */}
      <div className={styles.leftSection}>
        <div className={styles.iconsContainer}>
          <div className={styles.iconBlue}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L4 7V12C4 16.55 7.16 20.74 12 22C16.84 20.74 20 16.55 20 12V7L12 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div className={styles.iconGreen}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C7.59 20 4 16.41 4 12C4 7.59 7.59 4 12 4C16.41 4 20 7.59 20 12C20 16.41 16.41 20 12 20Z" fill="white"/>
              <path d="M12 6C11.45 6 11 6.45 11 7V12C11 12.55 11.45 13 12 13C12.55 13 13 12.55 13 12V7C13 6.45 12.55 6 12 6Z" fill="white"/>
              <path d="M12 15C11.45 15 11 15.45 11 16C11 16.55 11.45 17 12 17C12.55 17 13 16.55 13 16C13 15.45 12.55 15 12 15Z" fill="white"/>
            </svg>
          </div>
        </div>
        
        <h1 className={styles.mainTitle}>
          AI-Driven Disease Risk Prediction System
        </h1>
        
        <p className={styles.description}>
          Protecting communities in post-flood areas through intelligent disease surveillance and early warning systems.
        </p>
        
        <div className={styles.statsContainer}>
          <div className={styles.statItem}>
            <div className={styles.statValue}>90%</div>
            <div className={styles.statLabel}>Accuracy</div>
          </div>
          <div className={styles.statItem}>
            <div className={styles.statValue}>90+</div>
            <div className={styles.statLabel}>Districts</div>
          </div>
        </div>
      </div>

      {/* Right Section - Login Form */}
      <div className={styles.rightSection}>
        <div className={styles.loginCard}>
          <h2 className={styles.welcomeTitle}>Welcome Back</h2>
          <p className={styles.welcomeSubtitle}>
            Sign in to access the disease prediction dashboard
          </p>
          
          <form onSubmit={handleSubmit} className={styles.loginForm}>
            <div className={styles.inputGroup}>
              <label htmlFor="email" className={styles.inputLabel}>
                Email address
              </label>
              <input
                type="email"
                id="email"
                className={styles.input}
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            
            <div className={styles.inputGroup}>
              <label htmlFor="password" className={styles.inputLabel}>
                Password
              </label>
              <input
                type="password"
                id="password"
                className={styles.input}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            
            <button type="submit" className={styles.loginButton}>
              Login
            </button>
          </form>
          
          <p className={styles.trustStatement}>
            Trusted by health workers, NGOs, and government officials across Pakistan
          </p>
          
          <div className={styles.affiliations}>
            <div className={styles.affiliationTag}>WHO</div>
            <div className={styles.affiliationTag}>NIH</div>
            <div className={styles.affiliationTag}>MOH Pakistan</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;

