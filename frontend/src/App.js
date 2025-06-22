import React, { useState, useEffect } from 'react';
import axios from 'axios';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Main App Component
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

  // Initial data load
  useEffect(() => {
    fetchDashboardStats();
    fetchProperties();
    fetchTenants();
    fetchPayments();
    fetchSettings();
    fetchReceipts();
  }, []);

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1 className="header-title">🏠 {settings?.app_name || 'Gestion Location Immobilière'}</h1>
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
              className={`nav-btn ${currentView === 'settings' ? 'active' : ''}`}
              onClick={() => setCurrentView('settings')}
            >
              ⚙️ Paramètres
            </button>
          </nav>
        </div>
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
          />
        )}
      </main>
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
function Payments({ payments, tenants, properties, settings, onRefresh }) {
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
      await axios.put(`${API}/payments/${paymentId}/mark-paid`);
      onRefresh();
    } catch (error) {
      console.error('Erreur lors du marquage du paiement:', error);
    }
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
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Settings Component
function Settings({ settings, currencies, onRefresh }) {
  const [formData, setFormData] = useState({
    currency: settings?.currency || 'EUR',
    app_name: settings?.app_name || 'Gestion Location Immobilière'
  });

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

export default App;