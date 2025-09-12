import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, { withCredentials: true });
      setUser(response.data);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = (redirectUrl) => {
    const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
    window.location.href = authUrl;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
      setUser(null);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const processSession = async (sessionId) => {
    try {
      const response = await axios.post(`${API}/auth/process-session`, 
        { session_id: sessionId }, 
        { withCredentials: true }
      );
      setUser(response.data.user);
      return true;
    } catch (error) {
      console.error('Session processing error:', error);
      return false;
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, processSession, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles = null }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

// Auth Handler Component
const AuthHandler = () => {
  const { processSession } = useAuth();
  const navigate = useNavigate();
  const [processing, setProcessing] = useState(true);

  useEffect(() => {
    const handleAuth = async () => {
      const fragment = window.location.hash.substring(1);
      const params = new URLSearchParams(fragment);
      const sessionId = params.get('session_id');

      if (sessionId) {
        const success = await processSession(sessionId);
        if (success) {
          // Clean URL and redirect to dashboard
          window.history.replaceState({}, document.title, window.location.pathname);
          navigate('/dashboard');
        } else {
          navigate('/login');
        }
      } else {
        navigate('/login');
      }
      setProcessing(false);
    };

    handleAuth();
  }, [processSession, navigate]);

  if (processing) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
          <p className="text-white">Processing authentication...</p>
        </div>
      </div>
    );
  }

  return null;
};

// Navigation Component
const Navigation = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <nav className="bg-gray-800 border-b border-green-500">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <span className="text-black font-bold text-sm">A</span>
              </div>
              <span className="ml-2 text-white font-bold text-lg">AURA</span>
            </div>
            <div className="ml-10 flex items-baseline space-x-4">
              <button onClick={() => navigate('/dashboard')} className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                Dashboard
              </button>
              <button onClick={() => navigate('/jobs')} className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                Jobs
              </button>
              <button onClick={() => navigate('/events')} className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                Events
              </button>
              {(user.role === 'manager' || user.role === 'admin') && (
                <button onClick={() => navigate('/management')} className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                  Management
                </button>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              {user.picture && (
                <img src={user.picture} alt="Profile" className="w-8 h-8 rounded-full" />
              )}
              <span className="text-white text-sm">{user.name}</span>
              <span className="text-green-400 text-xs capitalize bg-green-900 px-2 py-1 rounded">
                {user.role}
              </span>
            </div>
            <button 
              onClick={handleLogout}
              className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

// Landing Page
const LandingPage = () => {
  const { user, login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  const handleLogin = () => {
    const redirectUrl = `${window.location.origin}/dashboard`;
    login(redirectUrl);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900">
      {/* Header */}
      <header className="relative z-10 bg-gray-900/80 backdrop-blur-sm border-b border-green-500/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center shadow-lg">
                <span className="text-black font-bold text-xl">A</span>
              </div>
              <span className="ml-3 text-white font-bold text-2xl">AURA</span>
              <span className="ml-2 text-gray-400 text-sm">Virtual Trucking</span>
            </div>
            <button 
              onClick={handleLogin}
              className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-black font-semibold px-8 py-3 rounded-lg shadow-lg transform hover:scale-105 transition-all duration-200"
            >
              Join Now
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-20 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-green-500/10 to-transparent"></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="relative z-10">
              <h1 className="text-5xl lg:text-7xl font-bold text-white leading-tight">
                Welcome to <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-green-600">AURA</span>
              </h1>
              <p className="text-xl text-gray-300 mt-6 leading-relaxed">
                The premier virtual trucking company in ETS2 and ATS. Join our professional fleet of drivers 
                and experience realistic logistics operations with a dedicated community.
              </p>
              <div className="mt-8 flex flex-col sm:flex-row gap-4">
                <button 
                  onClick={handleLogin}
                  className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-black font-semibold px-8 py-4 rounded-lg shadow-lg transform hover:scale-105 transition-all duration-200"
                >
                  Start Your Journey
                </button>
                <a 
                  href="#features" 
                  className="border-2 border-green-500 text-green-400 hover:bg-green-500 hover:text-black font-semibold px-8 py-4 rounded-lg transition-all duration-200 text-center"
                >
                  Learn More
                </a>
              </div>
            </div>
            <div className="relative">
              <img 
                src="https://images.unsplash.com/photo-1591768793355-74d04bb6608f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwxfHx0cnVja2luZ3xlbnwwfHx8fDE3NTc2OTU1NTd8MA&ixlib=rb-4.1.0&q=85"
                alt="Professional Truck"
                className="rounded-2xl shadow-2xl w-full h-96 object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent rounded-2xl"></div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">Why Choose AURA?</h2>
            <p className="text-xl text-gray-300">Professional virtual trucking experience</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-gray-900/50 backdrop-blur-sm p-8 rounded-xl border border-green-500/30 hover:border-green-500/60 transition-all duration-200">
              <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-black" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Professional Operations</h3>
              <p className="text-gray-300">Realistic job assignments, convoy operations, and professional management systems.</p>
            </div>

            <div className="bg-gray-900/50 backdrop-blur-sm p-8 rounded-xl border border-green-500/30 hover:border-green-500/60 transition-all duration-200">
              <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-black" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Active Community</h3>
              <p className="text-gray-300">Join a vibrant community of truckers with regular events, convoys, and competitions.</p>
            </div>

            <div className="bg-gray-900/50 backdrop-blur-sm p-8 rounded-xl border border-green-500/30 hover:border-green-500/60 transition-all duration-200">
              <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-black" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Career Progression</h3>
              <p className="text-gray-300">Track your progress, earn experience points, and climb the ranks in our organization.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-4xl font-bold text-green-500 mb-2">50+</div>
              <div className="text-gray-300">Active Drivers</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-green-500 mb-2">10k+</div>
              <div className="text-gray-300">Miles Driven</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-green-500 mb-2">500+</div>
              <div className="text-gray-300">Deliveries</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-green-500 mb-2">100%</div>
              <div className="text-gray-300">Professional</div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 border-t border-green-500/30 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center mb-4 md:mb-0">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <span className="text-black font-bold text-sm">A</span>
              </div>
              <span className="ml-2 text-white font-bold text-lg">AURA Virtual Trucking</span>
            </div>
            <div className="text-gray-400 text-sm">
              © 2024 AURA Virtual Trucking Company. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

// Login Page
const LoginPage = () => {
  const { login } = useAuth();

  const handleLogin = () => {
    const redirectUrl = `${window.location.origin}/dashboard`;
    login(redirectUrl);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center">
      <div className="max-w-md w-full bg-gray-800 rounded-lg shadow-xl p-8 border border-green-500/30">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-black font-bold text-2xl">A</span>
          </div>
          <h2 className="text-2xl font-bold text-white">Welcome to AURA</h2>
          <p className="text-gray-400 mt-2">Sign in to access your driver dashboard</p>
        </div>
        
        <button 
          onClick={handleLogin}
          className="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-black font-semibold py-3 px-4 rounded-lg shadow-lg transform hover:scale-105 transition-all duration-200"
        >
          Sign in with Google
        </button>
      </div>
    </div>
  );
};

// Dashboard Components
const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentJobs, setRecentJobs] = useState([]);
  const [upcomingEvents, setUpcomingEvents] = useState([]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [statsRes, jobsRes, eventsRes] = await Promise.all([
          axios.get(`${API}/company/stats`, { withCredentials: true }),
          axios.get(`${API}/jobs?status=assigned`, { withCredentials: true }),
          axios.get(`${API}/events`, { withCredentials: true })
        ]);
        
        setStats(statsRes.data);
        setRecentJobs(jobsRes.data.slice(0, 5));
        setUpcomingEvents(eventsRes.data.slice(0, 3));
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      }
    };

    fetchDashboardData();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900">
      <Navigation />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Welcome back, {user?.name}!</h1>
          <p className="text-gray-400 mt-2">Here's what's happening at AURA today</p>
        </div>

        {/* Stats Grid */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-gray-800 rounded-lg p-6 border border-green-500/30">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Total Drivers</p>
                  <p className="text-2xl font-bold text-white">{stats.total_drivers}</p>
                </div>
                <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 border border-green-500/30">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Total Deliveries</p>
                  <p className="text-2xl font-bold text-white">{stats.total_deliveries}</p>
                </div>
                <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 2L3 7v11a1 1 0 001 1h3a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1h3a1 1 0 001-1V7l-7-5z" clipRule="evenodd" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 border border-green-500/30">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Distance (km)</p>
                  <p className="text-2xl font-bold text-white">{Math.round(stats.total_distance)}</p>
                </div>
                <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 border border-green-500/30">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Active Drivers</p>
                  <p className="text-2xl font-bold text-white">{stats.active_drivers}</p>
                </div>
                <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Recent Jobs and Events */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Jobs */}
          <div className="bg-gray-800 rounded-lg border border-green-500/30 overflow-hidden">
            <div className="p-6 border-b border-gray-700">
              <h2 className="text-xl font-bold text-white">Your Recent Jobs</h2>
            </div>
            <div className="p-6">
              {recentJobs.length > 0 ? (
                <div className="space-y-4">
                  {recentJobs.map((job) => (
                    <div key={job.id} className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
                      <div>
                        <h3 className="font-semibold text-white">{job.title}</h3>
                        <p className="text-sm text-gray-400">{job.origin_city} → {job.destination_city}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-green-500 font-semibold">{job.reward} XP</p>
                        <p className="text-xs text-gray-400">{job.distance} km</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400">No jobs assigned yet. Check the Jobs page for available opportunities!</p>
              )}
            </div>
          </div>

          {/* Upcoming Events */}
          <div className="bg-gray-800 rounded-lg border border-green-500/30 overflow-hidden">
            <div className="p-6 border-b border-gray-700">
              <h2 className="text-xl font-bold text-white">Upcoming Events</h2>
            </div>
            <div className="p-6">
              {upcomingEvents.length > 0 ? (
                <div className="space-y-4">
                  {upcomingEvents.map((event) => (
                    <div key={event.id} className="p-4 bg-gray-700 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold text-white">{event.title}</h3>
                        <span className="text-xs bg-green-900 text-green-400 px-2 py-1 rounded capitalize">
                          {event.event_type}
                        </span>
                      </div>
                      <p className="text-sm text-gray-400 mb-2">{event.location}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(event.date_time).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400">No upcoming events. Stay tuned for convoy announcements!</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Jobs Page
const JobsPage = () => {
  const { user } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await axios.get(`${API}/jobs`, { withCredentials: true });
        setJobs(response.data);
      } catch (error) {
        console.error('Error fetching jobs:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();
  }, []);

  const completeJob = async (jobId) => {
    try {
      await axios.post(`${API}/jobs/${jobId}/complete`, {}, { withCredentials: true });
      // Refresh jobs
      const response = await axios.get(`${API}/jobs`, { withCredentials: true });
      setJobs(response.data);
    } catch (error) {
      console.error('Error completing job:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900">
        <Navigation />
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Navigation />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Available Jobs</h1>
          <p className="text-gray-400 mt-2">Choose from available delivery jobs</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {jobs.map((job) => (
            <div key={job.id} className="bg-gray-800 rounded-lg border border-green-500/30 overflow-hidden">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-white text-lg">{job.title}</h3>
                  <span className={`text-xs px-2 py-1 rounded capitalize ${
                    job.status === 'available' ? 'bg-green-900 text-green-400' :
                    job.status === 'assigned' ? 'bg-yellow-900 text-yellow-400' :
                    job.status === 'delivered' ? 'bg-blue-900 text-blue-400' :
                    'bg-gray-700 text-gray-400'
                  }`}>
                    {job.status}
                  </span>
                </div>
                
                <div className="space-y-2 mb-4">
                  <p className="text-gray-300"><strong>Cargo:</strong> {job.cargo}</p>
                  <p className="text-gray-300"><strong>Route:</strong> {job.origin_city} → {job.destination_city}</p>
                  <p className="text-gray-300"><strong>Distance:</strong> {job.distance} km</p>
                  <p className="text-gray-300"><strong>Difficulty:</strong> {job.difficulty}</p>
                  {job.assigned_driver_name && (
                    <p className="text-gray-300"><strong>Driver:</strong> {job.assigned_driver_name}</p>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <div className="text-green-500 font-bold text-lg">{job.reward} XP</div>
                  {job.status === 'assigned' && job.assigned_driver_id === user?.id && (
                    <button 
                      onClick={() => completeJob(job.id)}
                      className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                    >
                      Complete Job
                    </button>
                  )}
                </div>

                {job.deadline && (
                  <div className="mt-3 text-xs text-gray-500">
                    Deadline: {new Date(job.deadline).toLocaleDateString()}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {jobs.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-400">No jobs available at the moment. Check back later!</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Events Page
const EventsPage = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const response = await axios.get(`${API}/events`, { withCredentials: true });
        setEvents(response.data);
      } catch (error) {
        console.error('Error fetching events:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, []);

  const joinEvent = async (eventId) => {
    try {
      await axios.post(`${API}/events/${eventId}/join`, {}, { withCredentials: true });
      // Refresh events
      const response = await axios.get(`${API}/events`, { withCredentials: true });
      setEvents(response.data);
    } catch (error) {
      console.error('Error joining event:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900">
        <Navigation />
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Navigation />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Company Events</h1>
          <p className="text-gray-400 mt-2">Join convoys, meetings, and competitions</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {events.map((event) => (
            <div key={event.id} className="bg-gray-800 rounded-lg border border-green-500/30 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-white text-xl">{event.title}</h3>
                <span className="text-xs bg-green-900 text-green-400 px-2 py-1 rounded capitalize">
                  {event.event_type}
                </span>
              </div>
              
              <p className="text-gray-300 mb-4">{event.description}</p>
              
              <div className="space-y-2 mb-4">
                <p className="text-gray-300"><strong>Date:</strong> {new Date(event.date_time).toLocaleString()}</p>
                <p className="text-gray-300"><strong>Location:</strong> {event.location}</p>
                {event.max_participants && (
                  <p className="text-gray-300">
                    <strong>Participants:</strong> {event.participants.length}/{event.max_participants}
                  </p>
                )}
              </div>

              <button 
                onClick={() => joinEvent(event.id)}
                className="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg font-medium transition-colors"
              >
                Join Event
              </button>
            </div>
          ))}
        </div>

        {events.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-400">No events scheduled at the moment. Stay tuned for upcoming convoys!</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Management Page (for managers and admins)
const ManagementPage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [events, setEvents] = useState([]);
  const [showCreateJob, setShowCreateJob] = useState(false);
  const [showCreateEvent, setShowCreateEvent] = useState(false);
  const [newJob, setNewJob] = useState({
    title: '',
    description: '',
    cargo: '',
    origin_city: '',
    destination_city: '',
    distance: '',
    reward: '',
    difficulty: 'Easy'
  });
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    event_type: 'convoy',
    date_time: '',
    location: '',
    max_participants: ''
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [usersRes, jobsRes, eventsRes] = await Promise.all([
          axios.get(`${API}/users`, { withCredentials: true }),
          axios.get(`${API}/jobs`, { withCredentials: true }),
          axios.get(`${API}/events`, { withCredentials: true })
        ]);
        
        setUsers(usersRes.data);
        setJobs(jobsRes.data);
        setEvents(eventsRes.data);
      } catch (error) {
        console.error('Error fetching management data:', error);
      }
    };

    fetchData();
  }, []);

  const createJob = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/jobs`, {
        ...newJob,
        distance: parseFloat(newJob.distance),
        reward: parseInt(newJob.reward)
      }, { withCredentials: true });
      
      // Refresh data
      const jobsRes = await axios.get(`${API}/jobs`, { withCredentials: true });
      setJobs(jobsRes.data);
      
      // Reset form
      setNewJob({
        title: '',
        description: '',
        cargo: '',
        origin_city: '',
        destination_city: '',
        distance: '',
        reward: '',
        difficulty: 'Easy'
      });
      setShowCreateJob(false);
    } catch (error) {
      console.error('Error creating job:', error);
    }
  };

  const createEvent = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/events`, {
        ...newEvent,
        date_time: new Date(newEvent.date_time).toISOString(),
        max_participants: newEvent.max_participants ? parseInt(newEvent.max_participants) : null
      }, { withCredentials: true });
      
      // Refresh data
      const eventsRes = await axios.get(`${API}/events`, { withCredentials: true });
      setEvents(eventsRes.data);
      
      // Reset form
      setNewEvent({
        title: '',
        description: '',
        event_type: 'convoy',
        date_time: '',
        location: '',
        max_participants: ''
      });
      setShowCreateEvent(false);
    } catch (error) {
      console.error('Error creating event:', error);
    }
  };

  const updateUserRole = async (userId, newRole) => {
    try {
      await axios.put(`${API}/users/${userId}`, { role: newRole }, { withCredentials: true });
      // Refresh users
      const usersRes = await axios.get(`${API}/users`, { withCredentials: true });
      setUsers(usersRes.data);
    } catch (error) {
      console.error('Error updating user role:', error);
    }
  };

  const assignJob = async (jobId, driverId) => {
    try {
      await axios.post(`${API}/jobs/${jobId}/assign/${driverId}`, {}, { withCredentials: true });
      // Refresh jobs
      const jobsRes = await axios.get(`${API}/jobs`, { withCredentials: true });
      setJobs(jobsRes.data);
    } catch (error) {
      console.error('Error assigning job:', error);
    }
  };

  if (user?.role !== 'manager' && user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Navigation />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Management Dashboard</h1>
          <p className="text-gray-400 mt-2">Manage drivers, jobs, and events</p>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-8">
          <button 
            onClick={() => setActiveTab('users')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              activeTab === 'users' 
                ? 'bg-green-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Drivers
          </button>
          <button 
            onClick={() => setActiveTab('jobs')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              activeTab === 'jobs' 
                ? 'bg-green-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Jobs
          </button>
          <button 
            onClick={() => setActiveTab('events')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              activeTab === 'events' 
                ? 'bg-green-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Events
          </button>
        </div>

        {/* Content */}
        {activeTab === 'users' && (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg border border-green-500/30 overflow-hidden">
              <div className="p-6 border-b border-gray-700">
                <h2 className="text-xl font-bold text-white">Company Drivers</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Driver</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Role</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">XP</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Deliveries</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Distance</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {users.map((driver) => (
                      <tr key={driver.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            {driver.picture && (
                              <img src={driver.picture} alt="" className="w-8 h-8 rounded-full mr-3" />
                            )}
                            <div>
                              <div className="text-sm font-medium text-white">{driver.name}</div>
                              <div className="text-sm text-gray-400">{driver.email}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <select 
                            value={driver.role}
                            onChange={(e) => updateUserRole(driver.id, e.target.value)}
                            className="bg-gray-700 border border-gray-600 text-white text-sm rounded px-2 py-1"
                          >
                            <option value="driver">Driver</option>
                            <option value="manager">Manager</option>
                            <option value="admin">Admin</option>
                          </select>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-white">{driver.experience_points}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-white">{driver.total_deliveries}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-white">{Math.round(driver.total_distance)} km</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button 
                            className="text-green-400 hover:text-green-300 mr-3"
                            onClick={() => {/* View driver details */}}
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'jobs' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-white">Job Management</h2>
              <button 
                onClick={() => setShowCreateJob(true)}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium"
              >
                Create New Job
              </button>
            </div>

            {/* Create Job Modal */}
            {showCreateJob && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl mx-4 border border-green-500/30">
                  <h3 className="text-xl font-bold text-white mb-4">Create New Job</h3>
                  <form onSubmit={createJob} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <input
                        type="text"
                        placeholder="Job Title"
                        value={newJob.title}
                        onChange={(e) => setNewJob({...newJob, title: e.target.value})}
                        className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded"
                        required
                      />
                      <input
                        type="text"
                        placeholder="Cargo Type"
                        value={newJob.cargo}
                        onChange={(e) => setNewJob({...newJob, cargo: e.target.value})}
                        className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded"
                        required
                      />
                      <input
                        type="text"
                        placeholder="Origin City"
                        value={newJob.origin_city}
                        onChange={(e) => setNewJob({...newJob, origin_city: e.target.value})}
                        className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded"
                        required
                      />
                      <input
                        type="text"
                        placeholder="Destination City"
                        value={newJob.destination_city}
                        onChange={(e) => setNewJob({...newJob, destination_city: e.target.value})}
                        className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded"
                        required
                      />
                      <input
                        type="number"
                        placeholder="Distance (km)"
                        value={newJob.distance}
                        onChange={(e) => setNewJob({...newJob, distance: e.target.value})}
                        className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded"
                        required
                      />
                      <input
                        type="number"
                        placeholder="Reward (XP)"
                        value={newJob.reward}
                        onChange={(e) => setNewJob({...newJob, reward: e.target.value})}
                        className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded"
                        required
                      />
                      <select
                        value={newJob.difficulty}
                        onChange={(e) => setNewJob({...newJob, difficulty: e.target.value})}
                        className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded"
                      >
                        <option value="Easy">Easy</option>
                        <option value="Medium">Medium</option>
                        <option value="Hard">Hard</option>
                      </select>
                    </div>
                    <textarea
                      placeholder="Job Description"
                      value={newJob.description}
                      onChange={(e) => setNewJob({...newJob, description: e.target.value})}
                      className="w-full bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded h-24"
                      required
                    />
                    <div className="flex justify-end space-x-3">
                      <button 
                        type="button"
                        onClick={() => setShowCreateJob(false)}
                        className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded"
                      >
                        Cancel
                      </button>
                      <button 
                        type="submit"
                        className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
                      >
                        Create Job
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {jobs.map((job) => (
                <div key={job.id} className="bg-gray-800 rounded-lg border border-green-500/30 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-bold text-white">{job.title}</h3>
                    <span className={`text-xs px-2 py-1 rounded capitalize ${
                      job.status === 'available' ? 'bg-green-900 text-green-400' :
                      job.status === 'assigned' ? 'bg-yellow-900 text-yellow-400' :
                      job.status === 'delivered' ? 'bg-blue-900 text-blue-400' :
                      'bg-gray-700 text-gray-400'
                    }`}>
                      {job.status}
                    </span>
                  </div>
                  <div className="space-y-2 mb-4">
                    <p className="text-gray-300 text-sm">{job.origin_city} → {job.destination_city}</p>
                    <p className="text-gray-300 text-sm">{job.distance} km • {job.reward} XP</p>
                    {job.assigned_driver_name && (
                      <p className="text-gray-300 text-sm">Driver: {job.assigned_driver_name}</p>
                    )}
                  </div>
                  {job.status === 'available' && (
                    <select 
                      onChange={(e) => e.target.value && assignJob(job.id, e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded text-sm"
                      defaultValue=""
                    >
                      <option value="">Assign to Driver</option>
                      {users.filter(u => u.role === 'driver' || u.role === 'manager').map(driver => (
                        <option key={driver.id} value={driver.id}>{driver.name}</option>
                      ))}
                    </select>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'events' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-white">Event Management</h2>
              <button 
                onClick={() => setShowCreateEvent(true)}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium"
              >
                Create New Event
              </button>
            </div>

            {/* Create Event Modal */}
            {showCreateEvent && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl mx-4 border border-green-500/30">
                  <h3 className="text-xl font-bold text-white mb-4">Create New Event</h3>
                  <form onSubmit={createEvent} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <input
                        type="text"
                        placeholder="Event Title"
                        value={newEvent.title}
                        onChange={(e) => setNewEvent({...newEvent, title: e.target.value})}
                        className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded"
                        required
                      />
                      <select
                        value={newEvent.event_type}
                        onChange={(e) => setNewEvent({...newEvent, event_type: e.target.value})}
                        className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded"
                      >
                        <option value="convoy">Convoy</option>
                        <option value="meeting">Meeting</option>
                        <option value="training">Training</option>
                        <option value="competition">Competition</option>
                      </select>
                      <input
                        type="datetime-local"
                        value={newEvent.date_time}
                        onChange={(e) => setNewEvent({...newEvent, date_time: e.target.value})}
                        className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded"
                        required
                      />
                      <input
                        type="text"
                        placeholder="Location/Route"
                        value={newEvent.location}
                        onChange={(e) => setNewEvent({...newEvent, location: e.target.value})}
                        className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded"
                        required
                      />
                      <input
                        type="number"
                        placeholder="Max Participants (optional)"
                        value={newEvent.max_participants}
                        onChange={(e) => setNewEvent({...newEvent, max_participants: e.target.value})}
                        className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded"
                      />
                    </div>
                    <textarea
                      placeholder="Event Description"
                      value={newEvent.description}
                      onChange={(e) => setNewEvent({...newEvent, description: e.target.value})}
                      className="w-full bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded h-24"
                      required
                    />
                    <div className="flex justify-end space-x-3">
                      <button 
                        type="button"
                        onClick={() => setShowCreateEvent(false)}
                        className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded"
                      >
                        Cancel
                      </button>
                      <button 
                        type="submit"
                        className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
                      >
                        Create Event
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {events.map((event) => (
                <div key={event.id} className="bg-gray-800 rounded-lg border border-green-500/30 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-bold text-white">{event.title}</h3>
                    <span className="text-xs bg-green-900 text-green-400 px-2 py-1 rounded capitalize">
                      {event.event_type}
                    </span>
                  </div>
                  <p className="text-gray-300 mb-4">{event.description}</p>
                  <div className="space-y-2">
                    <p className="text-gray-300 text-sm">Date: {new Date(event.date_time).toLocaleString()}</p>
                    <p className="text-gray-300 text-sm">Location: {event.location}</p>
                    <p className="text-gray-300 text-sm">Participants: {event.participants.length}
                      {event.max_participants && ` / ${event.max_participants}`}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const location = useLocation();

  // Check for session_id in URL fragment
  useEffect(() => {
    const fragment = window.location.hash.substring(1);
    const params = new URLSearchParams(fragment);
    const sessionId = params.get('session_id');
    
    if (sessionId && location.pathname !== '/auth-handler') {
      window.location.replace('/auth-handler' + window.location.hash);
    }
  }, [location]);

  return (
    <div className="App">
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/auth-handler" element={<AuthHandler />} />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/jobs" element={
            <ProtectedRoute>
              <JobsPage />
            </ProtectedRoute>
          } />
          <Route path="/events" element={
            <ProtectedRoute>
              <EventsPage />
            </ProtectedRoute>
          } />
          <Route path="/management" element={
            <ProtectedRoute allowedRoles={['manager', 'admin']}>
              <ManagementPage />
            </ProtectedRoute>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </div>
  );
}

export default function AppWrapper() {
  return (
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
}