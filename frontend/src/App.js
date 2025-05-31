import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';

// Import all components
import Header from './components/Header';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import PostLostPage from './pages/PostLostPage';
import PostFoundPage from './pages/PostFoundPage';
import BrowseLostPage from './pages/BrowseLostPage';
import BrowseFoundPage from './pages/BrowseFoundPage';
import ItemDetailPage from './pages/ItemDetailPage';
import DashboardPage from './pages/DashboardPage';
import AdminDashboard from './pages/AdminDashboard';

// Import API services
import { 
  authAPI, 
  itemsAPI, 
  isAuthenticated, 
  getCurrentUserFromStorage,
  healthCheck
} from './services/api';

// User context
const UserContext = React.createContext();

function App() {
  const [user, setUser] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check authentication status on app load
  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Check backend health
        await healthCheck();
        
        // Check if user is authenticated
        if (isAuthenticated()) {
          const storedUser = getCurrentUserFromStorage();
          if (storedUser) {
            try {
              // Verify token is still valid by fetching current user
              const currentUser = await authAPI.getCurrentUser();
              setUser(currentUser);
            } catch (error) {
              // Token is invalid, clear storage
              authAPI.logout();
              setUser(null);
            }
          }
        }
        
        // Load public items (active items for browsing)
        await loadItems();
        
      } catch (error) {
        console.error('Failed to initialize app:', error);
        setError('Failed to connect to the backend. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    initializeApp();
  }, []);

  const loadItems = async (filters = {}) => {
    try {
      const fetchedItems = await itemsAPI.getItems({
        status: 'active',
        ...filters
      });
      setItems(fetchedItems);
    } catch (error) {
      console.error('Failed to load items:', error);
      setError('Failed to load items. Please try again.');
    }
  };

  const addItem = async (newItem) => {
    try {
      const createdItem = await itemsAPI.createItem(newItem);
      
      // Add to local state for immediate UI update
      setItems(prevItems => [createdItem, ...prevItems]);
      
      return createdItem.id;
    } catch (error) {
      console.error('Failed to create item:', error);
      throw new Error('Failed to create item. Please try again.');
    }
  };

  const updateItem = async (itemId, updateData) => {
    try {
      const updatedItem = await itemsAPI.updateItem(itemId, updateData);
      
      // Update local state
      setItems(prevItems => 
        prevItems.map(item => 
          item.id === itemId ? updatedItem : item
        )
      );
      
      return updatedItem;
    } catch (error) {
      console.error('Failed to update item:', error);
      throw new Error('Failed to update item. Please try again.');
    }
  };

  const login = async (credentials) => {
    try {
      const response = await authAPI.login(credentials);
      setUser(response.user);
      return response;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData);
      setUser(response.user);
      return response;
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const logout = () => {
    authAPI.logout();
    setUser(null);
    // Reload items to show only public ones
    loadItems();
  };

  // Admin route guard
  const AdminRoute = ({ children }) => {
    if (!user) return <Navigate to="/login" />;
    if (!user.is_admin) return <Navigate to="/dashboard" />;
    return children;
  };

  // Protected route guard
  const ProtectedRoute = ({ children }) => {
    if (!user) return <Navigate to="/login" />;
    return children;
  };

  // Loading screen
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Lost & Found Portal...</p>
        </div>
      </div>
    );
  }

  // Error screen
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 via-red-50 to-red-100 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-red-800 mb-2">Connection Error</h1>
          <p className="text-red-600 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <UserContext.Provider value={{ 
      user, 
      setUser, 
      items, 
      setItems, 
      addItem, 
      updateItem,
      loadItems,
      login,
      register,
      logout
    }}>
      <div className="App min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <Router>
          <Header />
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <LoginPage />} />
              <Route path="/register" element={user ? <Navigate to="/dashboard" /> : <RegisterPage />} />
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              } />
              <Route path="/admin" element={
                <AdminRoute>
                  <AdminDashboard />
                </AdminRoute>
              } />
              <Route path="/post-lost" element={
                <ProtectedRoute>
                  <PostLostPage />
                </ProtectedRoute>
              } />
              <Route path="/post-found" element={
                <ProtectedRoute>
                  <PostFoundPage />
                </ProtectedRoute>
              } />
              <Route path="/lost-items" element={<BrowseLostPage />} />
              <Route path="/found-items" element={<BrowseFoundPage />} />
              <Route path="/item/:id" element={<ItemDetailPage />} />
            </Routes>
          </AnimatePresence>
        </Router>
      </div>
    </UserContext.Provider>
  );
}

export { UserContext };
export default App;