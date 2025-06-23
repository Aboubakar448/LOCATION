import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();
const useAuth = () => useContext(AuthContext);

// Auth Provider Component
function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserInfo();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUserInfo = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { username, password });
      const { access_token, user_info } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(user_info);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Erreur de connexion' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const value = {
    user,
    login,
    logout,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Login Component
function Login() {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    const result = await login(credentials.username, credentials.password);
    
    if (!result.success) {
      setError(result.message);
    }
    
    setIsLoading(false);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>🏠 Gestion Location Immobilière</h1>
          <p>Devise: <strong>FCFA</strong></p>
          <p>Connectez-vous avec votre compte</p>
        </div>
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label>Nom d'utilisateur</label>
            <input
              type="text"
              value={credentials.username}
              onChange={(e) => setCredentials({...credentials, username: e.target.value})}
              placeholder="Entrez votre nom d'utilisateur"
              required
            />
          </div>
          
          <div className="form-group">
            <label>Mot de passe</label>
            <input
              type="password"
              value={credentials.password}
              onChange={(e) => setCredentials({...credentials, password: e.target.value})}
              placeholder="Entrez votre mot de passe"
              required
            />
          </div>
          
          {error && <div className="error-message">{error}</div>}
          
          <button type="submit" disabled={isLoading} className="login-btn">
            {isLoading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>
        
        <div className="login-footer">
          <p><strong>Compte par défaut :</strong></p>
          <p>Utilisateur: <code>admin</code></p>
          <p>Mot de passe: <code>admin123</code></p>
          <small>Contactez votre administrateur pour créer votre compte personnel</small>
        </div>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  return (
    <MainApp />
  );
}

function MainApp() {
  // Simuler un utilisateur connecté pour la version simple
  const user = { full_name: "Utilisateur", role: "admin" };
  const loading = false;
  const logout = () => alert("Déconnexion simulée");
  
  const [currentView, setCurrentView] = useState('dashboard');
  const [dashboardStats, setDashboardStats] = useState(null);
  const [properties, setProperties] = useState([]);
  const [units, setUnits] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [payments, setPayments] = useState([]);
  const [receipts, setReceipts] = useState([]);
  const [tenantHistory, setTenantHistory] = useState([]);
  const [settings, setSettings] = useState(null);
  const [currencies, setCurrencies] = useState([]);
  const [loadingData, setLoadingData] = useState(false);
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
  // Backup data to phone (automatique)
  const autoBackup = async () => {
    try {
      const response = await axios.get(`${API}/backup`);
      const backupData = response.data;
      
      // Create filename with current date
      const now = new Date();
      const dateStr = now.toISOString().split('T')[0];
      const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '-');
      const filename = `gestion-location-auto-backup-${dateStr}-${timeStr}.json`;
      
      // Create and download file automatically
      const blob = new Blob([JSON.stringify(backupData, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      console.log(`✅ Sauvegarde automatique: ${filename}`);
    } catch (error) {
      console.error('Erreur lors de la sauvegarde automatique:', error);
    }
  };

  // Backup data to phone (manuel)
  const backupToPhone = async () => {
    try {
      setLoadingData(true);
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
      setLoadingData(false);
    }
  };

  // Restore data from phone
  const restoreFromPhone = async (file) => {
    try {
      setLoadingData(true);
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
      setLoadingData(false);
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

  // Fetch units
  const fetchUnits = async () => {
    try {
      const response = await axios.get(`${API}/units`);
      setUnits(response.data);
    } catch (error) {
      console.error('Erreur lors de la récupération des unités:', error);
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

  // Initial data load
  useEffect(() => {
    fetchDashboardStats();
    fetchProperties();
    fetchUnits();
    fetchTenants();
    fetchPayments();
    fetchSettings();
    fetchCurrencies();
    fetchReceipts();
  }, []);
  
  // Pas de vérification d'authentification pour la version simple

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1 className="header-title">🏠 {settings?.app_name || 'Gestion Location Immobilière'}</h1>
          <div className="header-right">
            <div className="user-info">
              <span>👤 {user.full_name}</span>
              <span className={`role-badge ${user.role}`}>{user.role}</span>
              <span>💰 FCFA</span>
              <span style={{background: 'rgba(72, 187, 120, 0.3)', padding: '0.5rem 1rem', borderRadius: '15px', fontSize: '0.875rem', color: '#276749'}}>
                🔄 Sauvegarde Auto
              </span>
            </div>
            <button onClick={logout} className="logout-btn">
              🚪 Déconnexion
            </button>
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
            className={`nav-btn ${currentView === 'units' ? 'active' : ''}`}
            onClick={() => setCurrentView('units')}
          >
            🏠 Appartements/Studios
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
            className={`nav-btn ${currentView === 'search' ? 'active' : ''}`}
            onClick={() => setCurrentView('search')}
          >
            🔍 Recherche Historique
          </button>
          {user.role === 'admin' && (
            <button 
              className={`nav-btn ${currentView === 'admin' ? 'active' : ''}`}
              onClick={() => setCurrentView('admin')}
            >
              👥 Gestion Utilisateurs
            </button>
          )}
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
            onRefresh={() => {
              fetchProperties();
              autoBackup();
            }}
          />
        )}
        {currentView === 'units' && (
          <Units 
            units={units}
            properties={properties} 
            settings={settings}
            onRefresh={() => {
              fetchUnits();
              autoBackup();
            }}
          />
        )}
        {currentView === 'tenants' && (
          <Tenants 
            tenants={tenants} 
            properties={properties}
            units={units}
            settings={settings}
            onRefresh={() => {
              fetchTenants();
              autoBackup();
            }}
          />
        )}
        {currentView === 'payments' && (
          <Payments 
            payments={payments} 
            tenants={tenants}
            properties={properties}
            settings={settings}
            onRefresh={() => {
              fetchPayments();
              autoBackup(); // Sauvegarde automatique
            }}
            onGenerateReceipt={async (payment, method, notes) => {
              const receipt = await generateReceipt(payment, method, notes);
              autoBackup(); // Sauvegarde automatique après génération de reçu
              return receipt;
            }}
          />
        )}
        {currentView === 'receipts' && (
          <Receipts 
            receipts={receipts}
            tenants={tenants}
            properties={properties}
            units={units}
            settings={settings}
            onRefresh={() => {
              fetchReceipts();
              autoBackup();
            }}
            setCurrentReceipt={setCurrentReceipt}
            setShowReceiptModal={setShowReceiptModal}
          />
        )}
        {currentView === 'search' && (
          <SearchHistory 
            properties={properties}
            units={units}
            tenants={tenants}
            settings={settings}
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
            loading={loadingData}
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

// Dashboard Component
function Dashboard({ stats, onRefresh }) {
  if (!stats) {
    return <div className="loading">Chargement des statistiques...</div>;
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>📊 Tableau de Bord</h2>
        <button className="refresh-btn" onClick={onRefresh}>🔄 Actualiser</button>
      </div>
      
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">🏢</div>
          <div className="stat-info">
            <div className="stat-value">{stats.total_properties}</div>
            <div className="stat-label">Propriétés</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">🏠</div>
          <div className="stat-info">
            <div className="stat-value">{stats.total_units}</div>
            <div className="stat-label">Appartements/Studios</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">🔑</div>
          <div className="stat-info">
            <div className="stat-value">{stats.occupied_units}</div>
            <div className="stat-label">Unités Occupées</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">👥</div>
          <div className="stat-info">
            <div className="stat-value">{stats.total_tenants}</div>
            <div className="stat-label">Locataires</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-info">
            <div className="stat-value">{stats.monthly_revenue.toFixed(2)}{stats.currency_symbol}</div>
            <div className="stat-label">Revenus Mensuels ({stats.currency})</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">⏰</div>
          <div className="stat-info">
            <div className="stat-value">{stats.pending_payments}</div>
            <div className="stat-label">Paiements en Attente</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">⚠️</div>
          <div className="stat-info">
            <div className="stat-value">{stats.overdue_payments}</div>
            <div className="stat-label">Paiements en Retard</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">📈</div>
          <div className="stat-info">
            <div className="stat-value">{stats.occupancy_rate}%</div>
            <div className="stat-label">Taux d'Occupation</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Properties Component
function Properties({ properties, settings, onRefresh }) {
  const [showForm, setShowForm] = useState(false);
  const [editingProperty, setEditingProperty] = useState(null);
  const [quickEditId, setQuickEditId] = useState(null);
  const [quickEditRent, setQuickEditRent] = useState('');
  const [formData, setFormData] = useState({
    address: '',
    monthly_rent: '',
    description: '',
    status: 'disponible'
  });

  const currencySymbol = settings?.currency === 'EUR' ? '€' : 
                         settings?.currency === 'USD' ? '$' : 
                         settings?.currency === 'XOF' ? 'CFA' : 
                         settings?.currency === 'MAD' ? 'DH' : 
                         settings?.currency === 'TND' ? 'DT' : 
                         settings?.currency === 'GBP' ? '£' : 
                         settings?.currency === 'CHF' ? 'CHF' : 
                         settings?.currency === 'CAD' ? 'C$' : '€';

  const handleQuickRentEdit = async (propertyId, newRent) => {
    try {
      const property = properties.find(p => p.id === propertyId);
      const data = {
        address: property.address,
        monthly_rent: parseFloat(newRent),
        description: property.description,
        status: property.status
      };

      await axios.put(`${API}/properties/${propertyId}`, data);
      setQuickEditId(null);
      setQuickEditRent('');
      onRefresh();
    } catch (error) {
      console.error('Erreur lors de la mise à jour du prix:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        monthly_rent: parseFloat(formData.monthly_rent)
      };

      if (editingProperty) {
        await axios.put(`${API}/properties/${editingProperty.id}`, data);
      } else {
        await axios.post(`${API}/properties`, data);
      }
      
      setShowForm(false);
      setEditingProperty(null);
      setFormData({ address: '', monthly_rent: '', description: '', status: 'disponible' });
      onRefresh();
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
    }
  };

  const handleEdit = (property) => {
    setEditingProperty(property);
    setFormData({
      address: property.address,
      monthly_rent: property.monthly_rent.toString(),
      description: property.description || '',
      status: property.status
    });
    setShowForm(true);
  };

  const handleDelete = async (propertyId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cette propriété ?')) {
      try {
        await axios.delete(`${API}/properties/${propertyId}`);
        onRefresh();
      } catch (error) {
        console.error('Erreur lors de la suppression:', error);
      }
    }
  };

  return (
    <div className="properties">
      <div className="section-header">
        <h2>🏢 Propriétés</h2>
        <button 
          className="add-btn"
          onClick={() => {
            setShowForm(true);
            setEditingProperty(null);
            setFormData({ address: '', monthly_rent: '', description: '', status: 'disponible' });
          }}
        >
          ➕ Ajouter Propriété
        </button>
      </div>

      {showForm && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>{editingProperty ? 'Modifier Propriété' : 'Nouvelle Propriété'}</h3>
            <form onSubmit={handleSubmit}>
              <input
                type="text"
                placeholder="Adresse"
                value={formData.address}
                onChange={(e) => setFormData({...formData, address: e.target.value})}
                required
              />
              <input
                type="number"
                placeholder={`Loyer mensuel (${currencySymbol})`}
                value={formData.monthly_rent}
                onChange={(e) => setFormData({...formData, monthly_rent: e.target.value})}
                required
              />
              <textarea
                placeholder="Description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
              />
              <select
                value={formData.status}
                onChange={(e) => setFormData({...formData, status: e.target.value})}
              >
                <option value="disponible">Disponible</option>
                <option value="occupé">Occupé</option>
                <option value="maintenance">Maintenance</option>
              </select>
              <div className="form-actions">
                <button type="submit">{editingProperty ? 'Modifier' : 'Ajouter'}</button>
                <button type="button" onClick={() => setShowForm(false)}>Annuler</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="cards-grid">
        {properties.map(property => (
          <div key={property.id} className="property-card">
            <div className="card-header">
              <h3>{property.address}</h3>
              <span className={`status ${property.status}`}>
                {property.status}
              </span>
            </div>
            <div className="card-content">
              <div className="rent-section">
                {quickEditId === property.id ? (
                  <div className="quick-edit">
                    <input
                      type="number"
                      value={quickEditRent}
                      onChange={(e) => setQuickEditRent(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          handleQuickRentEdit(property.id, quickEditRent);
                        }
                      }}
                      placeholder="Nouveau prix"
                      autoFocus
                    />
                    <button 
                      onClick={() => handleQuickRentEdit(property.id, quickEditRent)}
                      className="quick-save-btn"
                    >
                      ✓
                    </button>
                    <button 
                      onClick={() => {
                        setQuickEditId(null);
                        setQuickEditRent('');
                      }}
                      className="quick-cancel-btn"
                    >
                      ✕
                    </button>
                  </div>
                ) : (
                  <div className="rent-display">
                    <p className="rent">💰 {property.monthly_rent}{currencySymbol}/mois</p>
                    <button 
                      className="quick-edit-btn"
                      onClick={() => {
                        setQuickEditId(property.id);
                        setQuickEditRent(property.monthly_rent.toString());
                      }}
                      title="Modifier le prix rapidement"
                    >
                      ✏️
                    </button>
                  </div>
                )}
              </div>
              {property.description && <p className="description">{property.description}</p>}
            </div>
            <div className="card-actions">
              <button onClick={() => handleEdit(property)}>✏️ Modifier</button>
              <button onClick={() => handleDelete(property.id)} className="delete-btn">🗑️ Supprimer</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Tenants Component
function Tenants({ tenants, properties, settings, onRefresh }) {
  const currencySymbol = settings?.currency === 'EUR' ? '€' : 
                         settings?.currency === 'USD' ? '$' : 
                         settings?.currency === 'XOF' ? 'CFA' : 
                         settings?.currency === 'MAD' ? 'DH' : 
                         settings?.currency === 'TND' ? 'DT' : 
                         settings?.currency === 'GBP' ? '£' : 
                         settings?.currency === 'CHF' ? 'CHF' : 
                         settings?.currency === 'CAD' ? 'C$' : '€';
  const [showForm, setShowForm] = useState(false);
  const [editingTenant, setEditingTenant] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    property_id: '',
    start_date: '',
    monthly_rent: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        monthly_rent: formData.monthly_rent ? parseFloat(formData.monthly_rent) : null,
        start_date: formData.start_date || null
      };

      if (editingTenant) {
        await axios.put(`${API}/tenants/${editingTenant.id}`, data);
      } else {
        await axios.post(`${API}/tenants`, data);
      }
      
      setShowForm(false);
      setEditingTenant(null);
      setFormData({ name: '', email: '', phone: '', property_id: '', start_date: '', monthly_rent: '' });
      onRefresh();
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
    }
  };

  const handleEdit = (tenant) => {
    setEditingTenant(tenant);
    setFormData({
      name: tenant.name,
      email: tenant.email || '',
      phone: tenant.phone || '',
      property_id: tenant.property_id || '',
      start_date: tenant.start_date || '',
      monthly_rent: tenant.monthly_rent ? tenant.monthly_rent.toString() : ''
    });
    setShowForm(true);
  };

  const handleDelete = async (tenantId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce locataire ?')) {
      try {
        await axios.delete(`${API}/tenants/${tenantId}`);
        onRefresh();
      } catch (error) {
        console.error('Erreur lors de la suppression:', error);
      }
    }
  };

  const getPropertyAddress = (propertyId) => {
    const property = properties.find(p => p.id === propertyId);
    return property ? property.address : 'Non assigné';
  };

  return (
    <div className="tenants">
      <div className="section-header">
        <h2>👥 Locataires</h2>
        <button 
          className="add-btn"
          onClick={() => {
            setShowForm(true);
            setEditingTenant(null);
            setFormData({ name: '', email: '', phone: '', property_id: '', start_date: '', monthly_rent: '' });
          }}
        >
          ➕ Ajouter Locataire
        </button>
      </div>

      {showForm && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>{editingTenant ? 'Modifier Locataire' : 'Nouveau Locataire'}</h3>
            <form onSubmit={handleSubmit}>
              <input
                type="text"
                placeholder="Nom complet"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
              />
              <input
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
              />
              <input
                type="tel"
                placeholder="Téléphone"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
              />
              <select
                value={formData.property_id}
                onChange={(e) => setFormData({...formData, property_id: e.target.value})}
              >
                <option value="">Sélectionner une propriété</option>
                {properties.map(property => (
                  <option key={property.id} value={property.id}>
                    {property.address} - {property.monthly_rent}€/mois
                  </option>
                ))}
              </select>
              <input
                type="date"
                placeholder="Date de début"
                value={formData.start_date}
                onChange={(e) => setFormData({...formData, start_date: e.target.value})}
              />
              <input
                type="number"
                placeholder="Loyer mensuel (€)"
                value={formData.monthly_rent}
                onChange={(e) => setFormData({...formData, monthly_rent: e.target.value})}
              />
              <div className="form-actions">
                <button type="submit">{editingTenant ? 'Modifier' : 'Ajouter'}</button>
                <button type="button" onClick={() => setShowForm(false)}>Annuler</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="cards-grid">
        {tenants.map(tenant => (
          <div key={tenant.id} className="tenant-card">
            <div className="card-header">
              <h3>{tenant.name}</h3>
            </div>
            <div className="card-content">
              {tenant.email && <p>📧 {tenant.email}</p>}
              {tenant.phone && <p>📞 {tenant.phone}</p>}
              <p>🏠 {getPropertyAddress(tenant.property_id)}</p>
              {tenant.monthly_rent && <p>💰 {tenant.monthly_rent}{currencySymbol}/mois</p>}
              {tenant.start_date && <p>📅 Depuis le {tenant.start_date}</p>}
            </div>
            <div className="card-actions">
              <button onClick={() => handleEdit(tenant)}>✏️ Modifier</button>
              <button onClick={() => handleDelete(tenant.id)} className="delete-btn">🗑️ Supprimer</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Payments Component
function Payments({ payments, tenants, properties, settings, onRefresh, onGenerateReceipt }) {
  const [showForm, setShowForm] = useState(false);
  const [editingPayment, setEditingPayment] = useState(null);
  const [formData, setFormData] = useState({
    tenant_id: '',
    property_id: '',
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear(),
    amount: '',
    status: 'en_attente'
  });

  const currencySymbol = settings?.currency === 'EUR' ? '€' : 
                         settings?.currency === 'USD' ? '$' : 
                         settings?.currency === 'XOF' ? 'CFA' : 
                         settings?.currency === 'MAD' ? 'DH' : 
                         settings?.currency === 'TND' ? 'DT' : 
                         settings?.currency === 'GBP' ? '£' : 
                         settings?.currency === 'CHF' ? 'CHF' : 
                         settings?.currency === 'CAD' ? 'C$' : '€';

  const monthNames = [
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        amount: parseFloat(formData.amount),
        month: parseInt(formData.month),
        year: parseInt(formData.year)
      };

      if (editingPayment) {
        await axios.put(`${API}/payments/${editingPayment.id}`, data);
      } else {
        await axios.post(`${API}/payments`, data);
      }
      
      setShowForm(false);
      setEditingPayment(null);
      setFormData({
        tenant_id: '',
        property_id: '',
        month: new Date().getMonth() + 1,
        year: new Date().getFullYear(),
        amount: '',
        status: 'en_attente'
      });
      onRefresh();
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
    }
  };

  const markAsPaid = async (paymentId) => {
    try {
      const response = await axios.put(`${API}/payments/${paymentId}/mark-paid`);
      const updatedPayment = response.data;
      
      // Generate receipt automatically after marking as paid
      await onGenerateReceipt(updatedPayment, 'Espèces', 'Paiement marqué comme payé');
      
      onRefresh();
    } catch (error) {
      console.error('Erreur lors du marquage du paiement:', error);
    }
  };

  const handleGenerateReceipt = async (payment) => {
    if (payment.status !== 'payé') {
      alert('Le paiement doit être marqué comme payé avant de générer un reçu');
      return;
    }
    await onGenerateReceipt(payment);
  };

  const getTenantName = (tenantId) => {
    const tenant = tenants.find(t => t.id === tenantId);
    return tenant ? tenant.name : 'Inconnu';
  };

  const getPropertyAddress = (propertyId) => {
    const property = properties.find(p => p.id === propertyId);
    return property ? property.address : 'Inconnu';
  };

  return (
    <div className="payments">
      <div className="section-header">
        <h2>💰 Paiements</h2>
        <button 
          className="add-btn"
          onClick={() => {
            setShowForm(true);
            setEditingPayment(null);
            setFormData({
              tenant_id: '',
              property_id: '',
              month: new Date().getMonth() + 1,
              year: new Date().getFullYear(),
              amount: '',
              status: 'en_attente'
            });
          }}
        >
          ➕ Ajouter Paiement
        </button>
      </div>

      {showForm && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>{editingPayment ? 'Modifier Paiement' : 'Nouveau Paiement'}</h3>
            <form onSubmit={handleSubmit}>
              <select
                value={formData.tenant_id}
                onChange={(e) => setFormData({...formData, tenant_id: e.target.value})}
                required
              >
                <option value="">Sélectionner un locataire</option>
                {tenants.map(tenant => (
                  <option key={tenant.id} value={tenant.id}>
                    {tenant.name}
                  </option>
                ))}
              </select>
              <select
                value={formData.property_id}
                onChange={(e) => setFormData({...formData, property_id: e.target.value})}
                required
              >
                <option value="">Sélectionner une propriété</option>
                {properties.map(property => (
                  <option key={property.id} value={property.id}>
                    {property.address}
                  </option>
                ))}
              </select>
              <select
                value={formData.month}
                onChange={(e) => setFormData({...formData, month: e.target.value})}
                required
              >
                {monthNames.map((month, index) => (
                  <option key={index + 1} value={index + 1}>{month}</option>
                ))}
              </select>
              <input
                type="number"
                placeholder="Année"
                value={formData.year}
                onChange={(e) => setFormData({...formData, year: e.target.value})}
                required
              />
              <input
                type="number"
                placeholder={`Montant (${currencySymbol})`}
                value={formData.amount}
                onChange={(e) => setFormData({...formData, amount: e.target.value})}
                required
              />
              <select
                value={formData.status}
                onChange={(e) => setFormData({...formData, status: e.target.value})}
              >
                <option value="en_attente">En attente</option>
                <option value="payé">Payé</option>
                <option value="en_retard">En retard</option>
              </select>
              <div className="form-actions">
                <button type="submit">{editingPayment ? 'Modifier' : 'Ajouter'}</button>
                <button type="button" onClick={() => setShowForm(false)}>Annuler</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="payments-list">
        {payments.map(payment => (
          <div key={payment.id} className={`payment-item ${payment.status}`}>
            <div className="payment-info">
              <h4>{getTenantName(payment.tenant_id)}</h4>
              <p>{getPropertyAddress(payment.property_id)}</p>
              <p>{monthNames[payment.month - 1]} {payment.year}</p>
            </div>
            <div className="payment-amount">
              <span className="amount">{payment.amount}{currencySymbol}</span>
              <span className={`status ${payment.status}`}>
                {payment.status === 'payé' ? '✅ Payé' : 
                 payment.status === 'en_attente' ? '⏰ En attente' : '⚠️ En retard'}
              </span>
            </div>
            <div className="payment-actions">
              {payment.status !== 'payé' && (
                <button 
                  className="pay-btn"
                  onClick={() => markAsPaid(payment.id)}
                >
                  ✅ Marquer payé
                </button>
              )}
              {payment.status === 'payé' && (
                <button 
                  className="receipt-btn"
                  onClick={() => handleGenerateReceipt(payment)}
                >
                  🧾 Générer reçu
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Settings Component
function Settings({ settings, currencies, onRefresh, onBackup, onRestore, loading }) {
  const [formData, setFormData] = useState({
    currency: settings?.currency || 'EUR',
    app_name: settings?.app_name || 'Gestion Location Immobilière'
  });
  const [fileInputKey, setFileInputKey] = useState(0);

  useEffect(() => {
    if (settings) {
      setFormData({
        currency: settings.currency,
        app_name: settings.app_name
      });
    }
  }, [settings]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/settings`, formData);
      onRefresh();
      alert('Paramètres mis à jour avec succès !');
    } catch (error) {
      console.error('Erreur lors de la mise à jour des paramètres:', error);
      alert('Erreur lors de la mise à jour des paramètres');
    }
  };

  const handleFileRestore = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type === 'application/json') {
        onRestore(file);
        setFileInputKey(prev => prev + 1); // Reset file input
      } else {
        alert('❌ Veuillez sélectionner un fichier JSON de sauvegarde');
      }
    }
  };

  if (!settings) {
    return <div className="loading">Chargement des paramètres...</div>;
  }

  return (
    <div className="settings">
      <div className="section-header">
        <h2>⚙️ Paramètres de l'Application</h2>
      </div>

      <div className="settings-content">
        <div className="settings-card">
          <h3>📱 Sauvegarde Automatique Activée</h3>
          <div style={{background: '#c6f6d5', padding: '1rem', borderRadius: '12px', border: '2px solid #48bb78', marginBottom: '1rem'}}>
            <p style={{color: '#276749', margin: '0'}}>
              ✅ <strong>Sauvegarde automatique activée !</strong><br/>
              Vos données sont sauvegardées automatiquement sur votre appareil après chaque modification.
            </p>
          </div>
          
          <div className="backup-actions">
            <button 
              className="backup-btn"
              onClick={onBackup}
              disabled={loading}
            >
              {loading ? '⏳ Sauvegarde...' : '💾 Sauvegarde Manuelle Supplémentaire'}
            </button>
            
            <div className="restore-section">
              <label className="restore-label">
                📂 Restaurer depuis Téléphone
                <input
                  key={fileInputKey}
                  type="file"
                  accept=".json"
                  onChange={handleFileRestore}
                  className="restore-input"
                  disabled={loading}
                />
              </label>
              <p className="restore-hint">Sélectionnez un fichier .json de sauvegarde</p>
            </div>
          </div>
        </div>

        <div className="settings-card">
          <h3>Configuration Générale</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Nom de l'Application</label>
              <input
                type="text"
                value={formData.app_name}
                onChange={(e) => setFormData({...formData, app_name: e.target.value})}
                placeholder="Nom de votre application"
              />
            </div>
            
            <div className="form-group">
              <label>Devise par Défaut</label>
              <select
                value={formData.currency}
                onChange={(e) => setFormData({...formData, currency: e.target.value})}
              >
                {currencies.map(currency => (
                  <option key={currency.code} value={currency.code}>
                    {currency.symbol} - {currency.name} ({currency.code})
                  </option>
                ))}
              </select>
            </div>

            <button type="submit" className="save-settings-btn">
              💾 Sauvegarder les Paramètres
            </button>
          </form>
        </div>

        <div className="settings-card">
          <h3>Informations Actuelles</h3>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Devise Actuelle:</span>
              <span className="info-value">
                {currencies.find(c => c.code === settings.currency)?.symbol} - {settings.currency}
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Nom de l'App:</span>
              <span className="info-value">{settings.app_name}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Dernière Mise à Jour:</span>
              <span className="info-value">
                {new Date(settings.updated_at).toLocaleDateString('fr-FR')}
              </span>
            </div>
          </div>
        </div>

        <div className="settings-card">
          <h3>Guide d'utilisation des Reçus</h3>
          <div className="usage-guide">
            <div className="guide-item">
              <span className="guide-icon">📝</span>
              <div>
                <strong>Numéros automatiques:</strong>
                <p>Les reçus sont numérotés automatiquement au format REC-YYYYMM-XXXX</p>
              </div>
            </div>
            <div className="guide-item">
              <span className="guide-icon">🔍</span>
              <div>
                <strong>Recherche instantanée:</strong>
                <p>Tapez le nom d'un locataire pour voir tous ses reçus groupés</p>
              </div>
            </div>
            <div className="guide-item">
              <span className="guide-icon">💾</span>
              <div>
                <strong>Sauvegarde:</strong>
                <p>Toutes vos données sont sauvegardées directement sur votre téléphone</p>
              </div>
            </div>
          </div>
        </div>

        <div className="settings-card">
          <h3>Devises Disponibles</h3>
          <div className="currencies-grid">
            {currencies.map(currency => (
              <div 
                key={currency.code} 
                className={`currency-item ${settings.currency === currency.code ? 'active' : ''}`}
              >
                <span className="currency-symbol">{currency.symbol}</span>
                <span className="currency-code">{currency.code}</span>
                <span className="currency-name">{currency.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Receipts Component
function Receipts({ receipts, tenants, properties, settings, onRefresh, setCurrentReceipt, setShowReceiptModal }) {
  const [filterTenant, setFilterTenant] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [instantSearch, setInstantSearch] = useState('');

  // Real-time filtering
  const filteredReceipts = receipts.filter(receipt => {
    const matchesTenant = !filterTenant || receipt.tenant_id === filterTenant;
    const matchesSearch = !searchTerm || 
      receipt.receipt_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      receipt.tenant_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      receipt.property_address.toLowerCase().includes(searchTerm.toLowerCase());
    
    // Instant search by tenant name
    const matchesInstantSearch = !instantSearch || 
      receipt.tenant_name.toLowerCase().includes(instantSearch.toLowerCase());
    
    return matchesTenant && matchesSearch && matchesInstantSearch;
  });

  // Group receipts by tenant for better organization
  const receiptsByTenant = filteredReceipts.reduce((acc, receipt) => {
    const tenantName = receipt.tenant_name;
    if (!acc[tenantName]) {
      acc[tenantName] = [];
    }
    acc[tenantName].push(receipt);
    return acc;
  }, {});

  const getTenantTotal = (tenantReceipts) => {
    return tenantReceipts.reduce((total, receipt) => total + receipt.amount, 0);
  };

  const downloadPDF = async (receipt) => {
    const pdf = new jsPDF();
    
    // Header
    pdf.setFontSize(20);
    pdf.setFont(undefined, 'bold');
    pdf.text('REÇU DE PAIEMENT', 105, 30, { align: 'center' });
    
    // Receipt info
    pdf.setFontSize(12);
    pdf.setFont(undefined, 'normal');
    pdf.text(`N° de reçu: ${receipt.receipt_number}`, 20, 50);
    pdf.text(`Date: ${new Date(receipt.payment_date).toLocaleDateString('fr-FR')}`, 20, 60);
    
    // Tenant info
    pdf.setFont(undefined, 'bold');
    pdf.text('INFORMATIONS LOCATAIRE:', 20, 80);
    pdf.setFont(undefined, 'normal');
    pdf.text(`Nom: ${receipt.tenant_name}`, 20, 90);
    pdf.text(`Propriété: ${receipt.property_address}`, 20, 100);
    
    // Payment info
    pdf.setFont(undefined, 'bold');
    pdf.text('DÉTAILS DU PAIEMENT:', 20, 120);
    pdf.setFont(undefined, 'normal');
    const monthNames = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
      'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];
    pdf.text(`Période: ${monthNames[receipt.period_month - 1]} ${receipt.period_year}`, 20, 130);
    pdf.text(`Montant: ${receipt.amount}${receipt.currency_symbol}`, 20, 140);
    pdf.text(`Mode de paiement: ${receipt.payment_method}`, 20, 150);
    
    if (receipt.notes) {
      pdf.text(`Notes: ${receipt.notes}`, 20, 160);
    }
    
    // Footer
    pdf.setFontSize(10);
    pdf.text('Ce reçu confirme le paiement du loyer pour la période indiquée.', 105, 250, { align: 'center' });
    pdf.text(`Généré le ${new Date().toLocaleDateString('fr-FR')} à ${new Date().toLocaleTimeString('fr-FR')}`, 105, 260, { align: 'center' });
    
    pdf.save(`Recu_${receipt.receipt_number}.pdf`);
  };

  const printReceipt = (receipt) => {
    const printWindow = window.open('', '', 'height=600,width=800');
    const monthNames = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
      'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];
    
    printWindow.document.write(`
      <html>
        <head>
          <title>Reçu ${receipt.receipt_number}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            .receipt-number { font-size: 18px; font-weight: bold; }
            .section { margin-bottom: 20px; }
            .label { font-weight: bold; }
            .amount { font-size: 24px; font-weight: bold; color: #48bb78; }
            .footer { margin-top: 50px; text-align: center; font-size: 12px; color: #666; }
            @media print { body { margin: 0; } }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>REÇU DE PAIEMENT</h1>
            <div class="receipt-number">N° ${receipt.receipt_number}</div>
            <div>Date: ${new Date(receipt.payment_date).toLocaleDateString('fr-FR')}</div>
          </div>
          
          <div class="section">
            <div class="label">INFORMATIONS LOCATAIRE:</div>
            <div>Nom: ${receipt.tenant_name}</div>
            <div>Propriété: ${receipt.property_address}</div>
          </div>
          
          <div class="section">
            <div class="label">DÉTAILS DU PAIEMENT:</div>
            <div>Période: ${monthNames[receipt.period_month - 1]} ${receipt.period_year}</div>
            <div class="amount">Montant: ${receipt.amount}${receipt.currency_symbol}</div>
            <div>Mode de paiement: ${receipt.payment_method}</div>
            ${receipt.notes ? `<div>Notes: ${receipt.notes}</div>` : ''}
          </div>
          
          <div class="footer">
            <div>Ce reçu confirme le paiement du loyer pour la période indiquée.</div>
            <div>Généré le ${new Date().toLocaleDateString('fr-FR')} à ${new Date().toLocaleTimeString('fr-FR')}</div>
          </div>
        </body>
      </html>
    `);
    
    printWindow.document.close();
    printWindow.print();
  };

  return (
    <div className="receipts">
      <div className="section-header">
        <h2>🧾 Historique des Reçus</h2>
        <button className="refresh-btn" onClick={onRefresh}>🔄 Actualiser</button>
      </div>

      <div className="receipts-filters">
        <div className="instant-search">
          <input
            type="text"
            placeholder="🔍 Tapez le nom du locataire pour voir ses reçus..."
            value={instantSearch}
            onChange={(e) => setInstantSearch(e.target.value)}
            className="instant-search-input"
          />
          {instantSearch && (
            <button 
              className="clear-search"
              onClick={() => setInstantSearch('')}
            >
              ✕
            </button>
          )}
        </div>
        
        <input
          type="text"
          placeholder="Rechercher par N° de reçu, locataire ou propriété..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
        
        <select
          value={filterTenant}
          onChange={(e) => setFilterTenant(e.target.value)}
          className="filter-select"
        >
          <option value="">Tous les locataires</option>
          {tenants.map(tenant => (
            <option key={tenant.id} value={tenant.id}>{tenant.name}</option>
          ))}
        </select>
      </div>

      {instantSearch && (
        <div className="search-results-header">
          <h3>🔍 Résultats pour "{instantSearch}" ({filteredReceipts.length} reçu{filteredReceipts.length > 1 ? 's' : ''})</h3>
        </div>
      )}

      <div className="receipts-list">
        {filteredReceipts.length === 0 ? (
          <div className="no-receipts">
            {instantSearch ? (
              <>
                <p>Aucun reçu trouvé pour "{instantSearch}"</p>
                <p>Vérifiez l'orthographe du nom du locataire.</p>
              </>
            ) : (
              <>
                <p>Aucun reçu trouvé.</p>
                <p>Les reçus sont générés automatiquement lors du marquage des paiements comme payés.</p>
              </>
            )}
          </div>
        ) : instantSearch ? (
          // Show grouped results when searching by tenant name
          Object.entries(receiptsByTenant).map(([tenantName, tenantReceipts]) => (
            <div key={tenantName} className="tenant-receipts-group">
              <div className="tenant-group-header">
                <h4>👤 {tenantName} ({tenantReceipts.length} reçu{tenantReceipts.length > 1 ? 's' : ''})</h4>
                <div className="tenant-total">
                  Total: {getTenantTotal(tenantReceipts)}{settings?.currency === 'EUR' ? '€' : 
                          settings?.currency === 'USD' ? '$' : 
                          settings?.currency === 'XOF' ? 'CFA' : 
                          settings?.currency === 'MAD' ? 'DH' : 
                          settings?.currency === 'TND' ? 'DT' : 
                          settings?.currency === 'GBP' ? '£' : 
                          settings?.currency === 'CHF' ? 'CHF' : 
                          settings?.currency === 'CAD' ? 'C$' : '€'}
                </div>
              </div>
              {tenantReceipts.map(receipt => (
                <div key={receipt.id} className="receipt-item tenant-grouped">
                  <div className="receipt-info">
                    <h5>{receipt.receipt_number}</h5>
                    <p><strong>Propriété:</strong> {receipt.property_address}</p>
                    <p><strong>Période:</strong> {new Date(2023, receipt.period_month - 1).toLocaleDateString('fr-FR', { month: 'long' })} {receipt.period_year}</p>
                    <p><strong>Date de paiement:</strong> {new Date(receipt.payment_date).toLocaleDateString('fr-FR')}</p>
                  </div>
                  <div className="receipt-amount">
                    <span className="amount">{receipt.amount}{receipt.currency_symbol}</span>
                    <span className="method">{receipt.payment_method}</span>
                  </div>
                  <div className="receipt-actions">
                    <button 
                      className="print-btn"
                      onClick={() => printReceipt(receipt)}
                    >
                      🖨️ Imprimer
                    </button>
                    <button 
                      className="download-btn"
                      onClick={() => downloadPDF(receipt)}
                    >
                      📥 PDF
                    </button>
                    <button 
                      className="view-btn"
                      onClick={() => {
                        setCurrentReceipt(receipt);
                        setShowReceiptModal(true);
                      }}
                    >
                      👁️ Voir
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ))
        ) : (
          // Show regular list when not searching by tenant name
          filteredReceipts.map(receipt => (
            <div key={receipt.id} className="receipt-item">
              <div className="receipt-info">
                <h4>{receipt.receipt_number}</h4>
                <p><strong>Locataire:</strong> {receipt.tenant_name}</p>
                <p><strong>Propriété:</strong> {receipt.property_address}</p>
                <p><strong>Période:</strong> {new Date(2023, receipt.period_month - 1).toLocaleDateString('fr-FR', { month: 'long' })} {receipt.period_year}</p>
                <p><strong>Date de paiement:</strong> {new Date(receipt.payment_date).toLocaleDateString('fr-FR')}</p>
              </div>
              <div className="receipt-amount">
                <span className="amount">{receipt.amount}{receipt.currency_symbol}</span>
                <span className="method">{receipt.payment_method}</span>
              </div>
              <div className="receipt-actions">
                <button 
                  className="print-btn"
                  onClick={() => printReceipt(receipt)}
                >
                  🖨️ Imprimer
                </button>
                <button 
                  className="download-btn"
                  onClick={() => downloadPDF(receipt)}
                >
                  📥 PDF
                </button>
                <button 
                  className="view-btn"
                  onClick={() => {
                    setCurrentReceipt(receipt);
                    setShowReceiptModal(true);
                  }}
                >
                  👁️ Voir
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// Receipt Modal Component
function ReceiptModal({ receipt, onClose }) {
  const monthNames = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];

  const downloadPDF = async () => {
    const element = document.getElementById('receipt-content');
    const canvas = await html2canvas(element);
    const imgData = canvas.toDataURL('image/png');
    
    const pdf = new jsPDF();
    const imgWidth = 210;
    const pageHeight = 295;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    let heightLeft = imgHeight;
    
    let position = 0;
    
    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
    heightLeft -= pageHeight;
    
    while (heightLeft >= 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
    }
    
    pdf.save(`Recu_${receipt.receipt_number}.pdf`);
  };

  const printReceipt = () => {
    window.print();
  };

  return (
    <div className="modal-overlay receipt-modal-overlay">
      <div className="modal receipt-modal">
        <div className="modal-header">
          <h3>Reçu de Paiement</h3>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>
        
        <div id="receipt-content" className="receipt-content">
          <div className="receipt-header">
            <h2>REÇU DE PAIEMENT</h2>
            <div className="receipt-number">N° {receipt.receipt_number}</div>
            <div className="receipt-date">Date: {new Date(receipt.payment_date).toLocaleDateString('fr-FR')}</div>
          </div>
          
          <div className="receipt-section">
            <h4>INFORMATIONS LOCATAIRE</h4>
            <p><strong>Nom:</strong> {receipt.tenant_name}</p>
            <p><strong>Propriété:</strong> {receipt.property_address}</p>
          </div>
          
          <div className="receipt-section">
            <h4>DÉTAILS DU PAIEMENT</h4>
            <p><strong>Période:</strong> {monthNames[receipt.period_month - 1]} {receipt.period_year}</p>
            <p><strong>Montant:</strong> <span className="receipt-amount">{receipt.amount}{receipt.currency_symbol}</span></p>
            <p><strong>Mode de paiement:</strong> {receipt.payment_method}</p>
            {receipt.notes && <p><strong>Notes:</strong> {receipt.notes}</p>}
          </div>
          
          <div className="receipt-footer">
            <p>Ce reçu confirme le paiement du loyer pour la période indiquée.</p>
            <p>Généré le {new Date(receipt.created_at).toLocaleDateString('fr-FR')} à {new Date(receipt.created_at).toLocaleTimeString('fr-FR')}</p>
          </div>
        </div>
        
        <div className="receipt-actions">
          <button className="print-btn" onClick={printReceipt}>
            🖨️ Imprimer
          </button>
          <button className="download-btn" onClick={downloadPDF}>
            📥 Télécharger PDF
          </button>
          <button className="close-btn" onClick={onClose}>
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
}

// Units Component (Appartements/Studios)
function Units({ units, properties, settings, onRefresh }) {
  const [showForm, setShowForm] = useState(false);
  const [editingUnit, setEditingUnit] = useState(null);
  const [formData, setFormData] = useState({
    property_id: '',
    unit_number: '',
    unit_type: 'appartement',
    monthly_rent: '',
    bedrooms: '',
    bathrooms: '',
    surface_area: '',
    description: '',
    status: 'disponible'
  });

  const currencySymbol = settings?.currency === 'EUR' ? '€' : 
                         settings?.currency === 'USD' ? '$' : 
                         settings?.currency === 'XOF' ? 'CFA' : 
                         settings?.currency === 'MAD' ? 'DH' : 
                         settings?.currency === 'TND' ? 'DT' : 
                         settings?.currency === 'GBP' ? '£' : 
                         settings?.currency === 'CHF' ? 'CHF' : 
                         settings?.currency === 'CAD' ? 'C$' : 'CFA';

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        monthly_rent: parseFloat(formData.monthly_rent),
        bedrooms: formData.bedrooms ? parseInt(formData.bedrooms) : null,
        bathrooms: formData.bathrooms ? parseInt(formData.bathrooms) : null,
        surface_area: formData.surface_area ? parseFloat(formData.surface_area) : null
      };

      if (editingUnit) {
        await axios.put(`${API}/units/${editingUnit.id}`, data);
      } else {
        await axios.post(`${API}/units`, data);
      }
      
      setShowForm(false);
      setEditingUnit(null);
      setFormData({
        property_id: '',
        unit_number: '',
        unit_type: 'appartement',
        monthly_rent: '',
        bedrooms: '',
        bathrooms: '',
        surface_area: '',
        description: '',
        status: 'disponible'
      });
      onRefresh();
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
    }
  };

  const handleEdit = (unit) => {
    setEditingUnit(unit);
    setFormData({
      property_id: unit.property_id,
      unit_number: unit.unit_number,
      unit_type: unit.unit_type,
      monthly_rent: unit.monthly_rent.toString(),
      bedrooms: unit.bedrooms ? unit.bedrooms.toString() : '',
      bathrooms: unit.bathrooms ? unit.bathrooms.toString() : '',
      surface_area: unit.surface_area ? unit.surface_area.toString() : '',
      description: unit.description || '',
      status: unit.status
    });
    setShowForm(true);
  };

  const handleDelete = async (unitId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cette unité ?')) {
      try {
        await axios.delete(`${API}/units/${unitId}`);
        onRefresh();
      } catch (error) {
        console.error('Erreur lors de la suppression:', error);
      }
    }
  };

  const getPropertyName = (propertyId) => {
    const property = properties.find(p => p.id === propertyId);
    return property ? property.address : 'Propriété inconnue';
  };

  const getUnitTypeIcon = (type) => {
    switch(type) {
      case 'appartement': return '🏠';
      case 'studio': return '🏡';
      case 'maison': return '🏘️';
      case 'commerce': return '🏪';
      default: return '🏠';
    }
  };

  return (
    <div className="units">
      <div className="section-header">
        <h2>🏠 Appartements & Studios</h2>
        <button 
          className="add-btn"
          onClick={() => {
            setShowForm(true);
            setEditingUnit(null);
            setFormData({
              property_id: '',
              unit_number: '',
              unit_type: 'appartement',
              monthly_rent: '',
              bedrooms: '',
              bathrooms: '',
              surface_area: '',
              description: '',
              status: 'disponible'
            });
          }}
        >
          ➕ Ajouter Unité
        </button>
      </div>

      {showForm && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>{editingUnit ? 'Modifier Unité' : 'Nouvelle Unité'}</h3>
            <form onSubmit={handleSubmit}>
              <select
                value={formData.property_id}
                onChange={(e) => setFormData({...formData, property_id: e.target.value})}
                required
              >
                <option value="">Sélectionner une propriété</option>
                {properties.map(property => (
                  <option key={property.id} value={property.id}>
                    {property.address}
                  </option>
                ))}
              </select>
              
              <input
                type="text"
                placeholder="Numéro/Nom d'unité (ex: Apt 1, Studio A)"
                value={formData.unit_number}
                onChange={(e) => setFormData({...formData, unit_number: e.target.value})}
                required
              />
              
              <select
                value={formData.unit_type}
                onChange={(e) => setFormData({...formData, unit_type: e.target.value})}
                required
              >
                <option value="appartement">🏠 Appartement</option>
                <option value="studio">🏡 Studio</option>
                <option value="maison">🏘️ Maison</option>
                <option value="commerce">🏪 Commerce</option>
              </select>
              
              <input
                type="number"
                placeholder={`Loyer mensuel (${currencySymbol})`}
                value={formData.monthly_rent}
                onChange={(e) => setFormData({...formData, monthly_rent: e.target.value})}
                required
              />
              
              <input
                type="number"
                placeholder="Nombre de chambres"
                value={formData.bedrooms}
                onChange={(e) => setFormData({...formData, bedrooms: e.target.value})}
              />
              
              <input
                type="number"
                placeholder="Nombre de salles de bain"
                value={formData.bathrooms}
                onChange={(e) => setFormData({...formData, bathrooms: e.target.value})}
              />
              
              <input
                type="number"
                step="0.1"
                placeholder="Surface (m²)"
                value={formData.surface_area}
                onChange={(e) => setFormData({...formData, surface_area: e.target.value})}
              />
              
              <textarea
                placeholder="Description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
              />
              
              <select
                value={formData.status}
                onChange={(e) => setFormData({...formData, status: e.target.value})}
              >
                <option value="disponible">Disponible</option>
                <option value="occupé">Occupé</option>
                <option value="maintenance">Maintenance</option>
              </select>
              
              <div className="form-actions">
                <button type="submit">{editingUnit ? 'Modifier' : 'Ajouter'}</button>
                <button type="button" onClick={() => setShowForm(false)}>Annuler</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="cards-grid">
        {units.map(unit => (
          <div key={unit.id} className="unit-card">
            <div className="card-header">
              <h3>{getUnitTypeIcon(unit.unit_type)} {unit.unit_number}</h3>
              <span className={`status ${unit.status}`}>
                {unit.status}
              </span>
            </div>
            <div className="card-content">
              <p><strong>📍 Propriété:</strong> {getPropertyName(unit.property_id)}</p>
              <p className="rent">💰 {unit.monthly_rent}{currencySymbol}/mois</p>
              {unit.bedrooms && <p>🛏️ {unit.bedrooms} chambre{unit.bedrooms > 1 ? 's' : ''}</p>}
              {unit.bathrooms && <p>🚿 {unit.bathrooms} salle{unit.bathrooms > 1 ? 's' : ''} de bain</p>}
              {unit.surface_area && <p>📐 {unit.surface_area}m²</p>}
              {unit.description && <p className="description">{unit.description}</p>}
            </div>
            <div className="card-actions">
              <button onClick={() => handleEdit(unit)}>✏️ Modifier</button>
              <button onClick={() => handleDelete(unit.id)} className="delete-btn">🗑️ Supprimer</button>
            </div>
          </div>
        ))}
        
        {units.length === 0 && (
          <div className="no-data">
            <p>Aucune unité créée.</p>
            <p>Commencez par ajouter des appartements ou studios à vos propriétés.</p>
          </div>
        )}
      </div>
    </div>
  );
}

// SearchHistory Component
function SearchHistory({ properties, units, tenants, settings }) {
  const [searchDate, setSearchDate] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedUnitHistory, setSelectedUnitHistory] = useState(null);

  const searchByDate = async () => {
    if (!searchDate) {
      alert('Veuillez sélectionner une date');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/search/occupancy?date=${searchDate}`);
      setSearchResults(response.data);
    } catch (error) {
      console.error('Erreur lors de la recherche:', error);
      alert('Erreur lors de la recherche');
    } finally {
      setLoading(false);
    }
  };

  const getUnitHistory = async (unitId) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/search/unit-history/${unitId}`);
      setSelectedUnitHistory(response.data);
    } catch (error) {
      console.error('Erreur lors de la récupération de l\'historique:', error);
      alert('Erreur lors de la récupération de l\'historique');
    } finally {
      setLoading(false);
    }
  };

  const currencySymbol = settings?.currency === 'XOF' ? 'CFA' : '€';

  return (
    <div className="search-history">
      <div className="section-header">
        <h2>🔍 Recherche dans l'Historique</h2>
      </div>

      <div className="search-section">
        <div className="search-card">
          <h3>📅 Rechercher les Occupants par Date</h3>
          <p>Trouvez qui occupait quels appartements/studios à une date donnée</p>
          
          <div className="search-form">
            <input
              type="date"
              value={searchDate}
              onChange={(e) => setSearchDate(e.target.value)}
              className="date-input"
            />
            <button 
              onClick={searchByDate}
              disabled={loading}
              className="search-btn"
            >
              {loading ? '⏳ Recherche...' : '🔍 Rechercher'}
            </button>
          </div>

          {searchResults && (
            <div className="search-results">
              <h4>📋 Occupants le {new Date(searchResults.date).toLocaleDateString('fr-FR')}</h4>
              
              {searchResults.occupants.length === 0 ? (
                <p className="no-results">Aucun occupant trouvé pour cette date.</p>
              ) : (
                <div className="occupants-list">
                  {searchResults.occupants.map((occupant, index) => (
                    <div key={index} className="occupant-item">
                      <div className="occupant-info">
                        <h5>👤 {occupant.tenant_name}</h5>
                        <p>📞 {occupant.tenant_phone}</p>
                        <p>🏠 {occupant.property_name}</p>
                        <p>🏡 {occupant.unit_number} ({occupant.unit_type})</p>
                        <p>💰 {occupant.monthly_rent}{currencySymbol}/mois</p>
                        <p>📅 Du {new Date(occupant.start_date).toLocaleDateString('fr-FR')} 
                           {occupant.end_date ? ` au ${new Date(occupant.end_date).toLocaleDateString('fr-FR')}` : ' (en cours)'}
                        </p>
                        <p>💸 {occupant.months_paid} mois payé{occupant.months_paid > 1 ? 's' : ''}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="search-card">
          <h3>🏠 Historique des Unités</h3>
          <p>Consultez l'historique complet d'un appartement ou studio</p>
          
          <div className="units-grid">
            {units.map(unit => (
              <div key={unit.id} className="unit-history-item">
                <h5>{unit.unit_number}</h5>
                <p>{properties.find(p => p.id === unit.property_id)?.address}</p>
                <button 
                  onClick={() => getUnitHistory(unit.id)}
                  className="history-btn"
                >
                  📋 Voir Historique
                </button>
              </div>
            ))}
          </div>

          {selectedUnitHistory && (
            <div className="unit-history-results">
              <h4>📋 Historique de l'Unité</h4>
              
              {selectedUnitHistory.length === 0 ? (
                <p className="no-results">Aucun historique trouvé pour cette unité.</p>
              ) : (
                <div className="history-timeline">
                  {selectedUnitHistory.map((entry, index) => (
                    <div key={entry.id} className="timeline-item">
                      <div className="timeline-date">
                        {new Date(entry.created_at).toLocaleDateString('fr-FR')}
                      </div>
                      <div className="timeline-content">
                        <h6>{entry.tenant_name}</h6>
                        <p>{entry.action === 'moved_in' ? '🏠 Emménagement' : 
                            entry.action === 'moved_out' ? '📦 Déménagement' : 
                            '💰 Modification loyer'}</p>
                        <p>Du {new Date(entry.start_date).toLocaleDateString('fr-FR')} 
                           {entry.end_date ? ` au ${new Date(entry.end_date).toLocaleDateString('fr-FR')}` : ' (en cours)'}
                        </p>
                        <p>💰 {entry.monthly_rent}{currencySymbol}/mois</p>
                        <p>💸 {entry.months_paid} mois payé{entry.months_paid > 1 ? 's' : ''}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;