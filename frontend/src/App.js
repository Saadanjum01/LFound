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

// Mock data for demonstration
const MOCK_ITEMS = [
  {
    id: 1,
    type: 'lost',
    title: 'Blue iPhone 14 Pro',
    category: 'Electronics',
    description: 'Lost my blue iPhone 14 Pro near the library. Has a clear case with some stickers on the back.',
    location: 'Main Library',
    date: '2025-03-15',
    image: 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400',
    reward: 50,
    urgency: 'high',
    contact: 'john.doe@umt.edu',
    status: 'active'
  },
  {
    id: 2,
    type: 'found',
    title: 'Red Backpack',
    category: 'Bags',
    description: 'Found a red JanSport backpack in the cafeteria. Contains some textbooks and notebooks.',
    location: 'Student Cafeteria',
    date: '2025-03-14',
    image: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400',
    reward: 0,
    urgency: 'medium',
    contact: 'jane.smith@umt.edu',
    status: 'active'
  },
  {
    id: 3,
    type: 'lost',
    title: 'Silver MacBook Air',
    category: 'Electronics',
    description: 'Lost my MacBook Air in the computer science building. Has a "UMT CS" sticker on it.',
    location: 'Computer Science Building',
    date: '2025-03-13',
    image: 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400',
    reward: 100,
    urgency: 'high',
    contact: 'alex.johnson@umt.edu',
    status: 'active'
  },
  {
    id: 4,
    type: 'found',
    title: 'Black Wallet',
    category: 'Personal Items',
    description: 'Found a black leather wallet near the parking lot. Contains ID and some cards.',
    location: 'Parking Lot A',
    date: '2025-03-12',
    image: 'https://images.unsplash.com/photo-1627123424574-724758594e93?w=400',
    reward: 0,
    urgency: 'high',
    contact: 'sarah.wilson@umt.edu',
    status: 'active'
  },
  {
    id: 5,
    type: 'lost',
    title: 'Gold Ring',
    category: 'Jewelry',
    description: 'Lost my grandmother\'s gold ring in the gymnasium. Very sentimental value.',
    location: 'Main Gymnasium',
    date: '2025-03-11',
    image: 'https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=400',
    reward: 200,
    urgency: 'high',
    contact: 'mike.brown@umt.edu',
    status: 'active'
  },
  {
    id: 6,
    type: 'found',
    title: 'Blue Water Bottle',
    category: 'Personal Items',
    description: 'Found a blue Hydro Flask water bottle in the engineering building.',
    location: 'Engineering Building',
    date: '2025-03-10',
    image: 'https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=400',
    reward: 0,
    urgency: 'low',
    contact: 'lisa.davis@umt.edu',
    status: 'active'
  }
];

// User context
const UserContext = React.createContext();

function App() {
  const [user, setUser] = useState(null);
  const [items, setItems] = useState(MOCK_ITEMS);

  // Auto-login for demo purposes
  useEffect(() => {
    const demoUser = {
      id: 1,
      name: 'John Doe',
      email: 'john.doe@umt.edu',
      avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face',
      is_admin: true // Demo user has admin privileges
    };
    setUser(demoUser);
  }, []);

  const addItem = (newItem) => {
    const item = {
      ...newItem,
      id: Date.now(),
      date: new Date().toISOString().split('T')[0],
      status: 'active',
      contact: user?.email || 'user@umt.edu'
    };
    setItems([item, ...items]);
    return item.id;
  };

  // Admin route guard
  const AdminRoute = ({ children }) => {
    if (!user) return <Navigate to="/login" />;
    if (!user.is_admin) return <Navigate to="/dashboard" />;
    return children;
  };

  return (
    <UserContext.Provider value={{ user, setUser, items, setItems, addItem }}>
      <div className="App min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <Router>
          <Header />
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <LoginPage />} />
              <Route path="/register" element={user ? <Navigate to="/dashboard" /> : <RegisterPage />} />
              <Route path="/dashboard" element={user ? <DashboardPage /> : <Navigate to="/login" />} />
              <Route path="/admin" element={
                <AdminRoute>
                  <AdminDashboard />
                </AdminRoute>
              } />
              <Route path="/post-lost" element={user ? <PostLostPage /> : <Navigate to="/login" />} />
              <Route path="/post-found" element={user ? <PostFoundPage /> : <Navigate to="/login" />} />
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