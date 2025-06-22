import React, { useState, useEffect } from 'react';
import axios from 'axios';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Main App Component (Version Simple - Sans authentification)
function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [dashboardStats, setDashboardStats] = useState(null);
  const [properties, setProperties] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [payments, setPayments] = useState([]);
  const [receipts, setReceipts] = useState([]);
  const [settings, setSettings] = useState(null);
  const [currencies, setCurrencies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showReceiptModal, setShowReceiptModal] = useState(false);
  const [currentReceipt, setCurrentReceipt] = useState(null);

  // Fetch app settings
  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings(response.data);
    } catch (error) {
      console.error('Erreur lors de la récupération des paramètres:', error);
    }
  };

  // Fetch available currencies
  const fetchCurrencies = async () => {
    try {
      const response = await axios.get(`${API}/currencies`);
      setCurrencies(response.data.currencies);
    } catch (error) {
      console.error('Erreur lors de la récupération des devises:', error);
    }
  };

  // Fetch dashboard stats
  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard`);
      setDashboardStats(response.data);
    } catch (error) {
      console.error('Erreur lors de la récupération des statistiques:', error);
    }
  };

  // Fetch properties
  const fetchProperties = async () => {
    try {
      const response = await axios.get(`${API}/properties`);
      setProperties(response.data);
    } catch (error) {
      console.error('Erreur lors de la récupération des propriétés:', error);
    }
  };

  // Fetch tenants
  const fetchTenants = async () => {
    try {
      const response = await axios.get(`${API}/tenants`);
      setTenants(response.data);
    } catch (error) {
      console.error('Erreur lors de la récupération des locataires:', error);
    }
  };

  // Fetch payments
  const fetchPayments = async () => {
    try {
      const response = await axios.get(`${API}/payments`);
      setPayments(response.data);
    } catch (error) {
      console.error('Erreur lors de la récupération des paiements:', error);
    }
  };

  // Fetch receipts
  const fetchReceipts = async () => {
    try {
      const response = await axios.get(`${API}/receipts`);
      setReceipts(response.data);
    } catch (error) {
      console.error('Erreur lors de la récupération des reçus:', error);
    }
  };

  // Generate receipt
  const generateReceipt = async (payment, paymentMethod = 'Espèces', notes = '') => {
    try {
      const receiptData = {
        tenant_id: payment.tenant_id,
        payment_id: payment.id,
        payment_method: paymentMethod,
        notes: notes
      };

      const response = await axios.post(`${API}/receipts`, receiptData);
      const receipt = response.data;
      
      setCurrentReceipt(receipt);
      setShowReceiptModal(true);
      fetchReceipts();
      
      return receipt;
    } catch (error) {
      console.error('Erreur lors de la génération du reçu:', error);
      alert('Erreur lors de la génération du reçu');
    }
  };

  // Backup data to phone
  const backupToPhone = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/backup`);
      const backupData = response.data;
      
      // Create filename with current date
      const now = new Date();
      const dateStr = now.toISOString().split('T')[0];
      const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '-');
      const filename = `gestion-location-backup-${dateStr}-${timeStr}.json`;
      
      // Create and download file
      const blob = new Blob([JSON.stringify(backupData, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      alert(`✅ Sauvegarde téléchargée sur votre téléphone !\nFichier: ${filename}`);
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
      alert('❌ Erreur lors de la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  // Restore data from phone
  const restoreFromPhone = async (file) => {
    try {
      setLoading(true);
      const fileContent = await file.text();
      const backupData = JSON.parse(fileContent);
      
      const response = await axios.post(`${API}/restore`, backupData);
      
      // Refresh all data
      await Promise.all([
        fetchDashboardStats(),
        fetchProperties(),
        fetchTenants(),
        fetchPayments(),
        fetchReceipts(),
        fetchSettings()
      ]);
      
      alert(`✅ Données restaurées avec succès !\n${JSON.stringify(response.data.restored_records, null, 2)}`);
    } catch (error) {
      console.error('Erreur lors de la restauration:', error);
      alert('❌ Erreur lors de la restauration. Vérifiez le fichier de sauvegarde.');
    } finally {
      setLoading(false);
    }
  };

  // Initial data load
  useEffect(() => {
    fetchDashboardStats();
    fetchProperties();
    fetchTenants();
    fetchPayments();
    fetchSettings();
    fetchCurrencies();
    fetchReceipts();
  }, []);

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1 className="header-title">🏠 {settings?.app_name || 'Gestion Location Immobilière'}</h1>
          <div className="header-right">
            <div className="user-info">
              <span>💰 FCFA</span>
              <span style={{background: 'rgba(255,255,255,0.2)', padding: '0.5rem 1rem', borderRadius: '15px'}}>
                Version Simple - Accès Direct
              </span>
            </div>
          </div>
        </div>
        <nav className="nav">
          <button 
            className={`nav-btn ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentView('dashboard')}
          >
            📊 Tableau de Bord
          </button>
          <button 
            className={`nav-btn ${currentView === 'properties' ? 'active' : ''}`}
            onClick={() => setCurrentView('properties')}
          >
            🏢 Propriétés
          </button>
          <button 
            className={`nav-btn ${currentView === 'tenants' ? 'active' : ''}`}
            onClick={() => setCurrentView('tenants')}
          >
            👥 Locataires
          </button>
          <button 
            className={`nav-btn ${currentView === 'payments' ? 'active' : ''}`}
            onClick={() => setCurrentView('payments')}
          >
            💰 Paiements
          </button>
          <button 
            className={`nav-btn ${currentView === 'receipts' ? 'active' : ''}`}
            onClick={() => setCurrentView('receipts')}
          >
            🧾 Reçus
          </button>
          <button 
            className={`nav-btn ${currentView === 'settings' ? 'active' : ''}`}
            onClick={() => setCurrentView('settings')}
          >
            ⚙️ Paramètres
          </button>
        </nav>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {currentView === 'dashboard' && (
          <Dashboard 
            stats={dashboardStats} 
            onRefresh={fetchDashboardStats}
          />
        )}
        {currentView === 'properties' && (
          <Properties 
            properties={properties} 
            settings={settings}
            onRefresh={fetchProperties}
          />
        )}
        {currentView === 'tenants' && (
          <Tenants 
            tenants={tenants} 
            properties={properties}
            settings={settings}
            onRefresh={fetchTenants}
          />
        )}
        {currentView === 'payments' && (
          <Payments 
            payments={payments} 
            tenants={tenants}
            properties={properties}
            settings={settings}
            onRefresh={fetchPayments}
            onGenerateReceipt={generateReceipt}
          />
        )}
        {currentView === 'receipts' && (
          <Receipts 
            receipts={receipts}
            tenants={tenants}
            properties={properties}
            settings={settings}
            onRefresh={fetchReceipts}
            setCurrentReceipt={setCurrentReceipt}
            setShowReceiptModal={setShowReceiptModal}
          />
        )}
        {currentView === 'settings' && (
          <Settings 
            settings={settings}
            currencies={currencies}
            onRefresh={() => {
              fetchSettings();
              fetchDashboardStats();
            }}
            onBackup={backupToPhone}
            onRestore={restoreFromPhone}
            loading={loading}
          />
        )}
      </main>

      {/* Receipt Modal */}
      {showReceiptModal && currentReceipt && (
        <ReceiptModal 
          receipt={currentReceipt}
          onClose={() => {
            setShowReceiptModal(false);
            setCurrentReceipt(null);
          }}
        />
      )}
    </div>
  );
}

// Les autres composants restent identiques...
// (Dashboard, Properties, Tenants, Payments, Receipts, Settings, ReceiptModal)

// [Copier ici tous les autres composants du fichier App.js original...]

export default App;