# Project Structure

This document outlines the folder structure for the AI-Powered Disease Risk Predictor Frontend.

## 📁 Folder Structure

```
FYP-Frontend/
├── src/
│   ├── components/          # React components
│   │   ├── common/          # Reusable UI components (Button, Input, Card, Modal, etc.)
│   │   ├── layout/          # Layout components (Header, Footer, Sidebar, Navigation)
│   │   └── features/        # Feature-specific components
│   │
│   ├── pages/               # Page-level components (route components)
│   │
│   ├── services/            # API services and external integrations
│   │
│   ├── utils/               # Utility functions and helpers
│   │
│   ├── hooks/               # Custom React hooks
│   │
│   ├── context/             # React Context providers for state management
│   │
│   ├── assets/              # Static assets
│   │   ├── images/          # Image files
│   │   └── styles/          # Global styles, themes, CSS
│   │
│   ├── constants/           # Application-wide constants
│   │
│   ├── types/               # TypeScript types and interfaces (if using TypeScript)
│   │
│   └── config/              # Configuration files
│
├── public/                  # Public static files
└── package.json             # Dependencies and scripts
```

## 📋 Component Organization

### Common Components (`src/components/common/`)
Reusable UI components that can be used anywhere in the application:
- Buttons
- Input fields
- Cards
- Modals
- Loading spinners
- Alerts/Notifications
- etc.

### Layout Components (`src/components/layout/`)
Components that define the overall structure of pages:
- Header
- Footer
- Sidebar
- Navigation
- Main Layout wrapper

### Feature Components (`src/components/features/`)
Components specific to the disease prediction features:
- Prediction forms
- Results display
- Risk assessment components
- etc.

## 📄 Pages (`src/pages/`)
Each file in this folder represents a page/route in your application. Examples:
- HomePage.jsx
- PredictionPage.jsx
- ResultsPage.jsx
- AboutPage.jsx
- etc.

## 🔧 Best Practices

1. **Component Naming**: Use PascalCase for component files (e.g., `Button.jsx`, `DiseaseCard.jsx`)
2. **One Component Per File**: Each component should have its own file
3. **Index Files**: Use `index.js` files to export components for cleaner imports
4. **Separation of Concerns**: Keep business logic in services, UI in components
5. **Reusability**: Place reusable components in `common/`, feature-specific in `features/`

## 🚀 Next Steps

1. Install React and necessary dependencies
2. Set up routing (React Router)
3. Create initial components based on Figma designs
4. Set up API service layer
5. Implement state management (Context API or Redux)

