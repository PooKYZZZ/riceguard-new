import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import App from './App';
import DashboardPage from './pages/DashboardPage';
import EnhancedDashboardPage from './pages/EnhancedDashboardPage';
import ScanPage from './pages/ScanPage';
import HistoryPage from './pages/HistoryPage';
import DiseaseHeatmapPage from './pages/DiseaseHeatmapPage';
import SettingsPage from './pages/SettingsPage';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <ThemeProvider>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/dashboard-enhanced" element={<EnhancedDashboardPage />} />
        <Route path="/scan" element={<ScanPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/heatmap" element={<DiseaseHeatmapPage />} />
        <Route path="/analytics" element={<DiseaseHeatmapPage />} />
      </Routes>
    </BrowserRouter>
  </ThemeProvider>
);