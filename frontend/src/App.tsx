import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useParams, useNavigate, useLocation } from 'react-router-dom';
import EventDashboard from './components/EventDashboard';
import EventDetails from './components/EventDetails';
import DialogueRounds from './components/DialogueRounds';
import UnifiedDashboard from './components/UnifiedDashboard';
import LandingPage from './components/LandingPage';
import SignIn from './components/SignIn';
import Logo from './components/Logo';
import EventWizard from './components/EventWizard';
import TemplateManager from './components/TemplateManager';
import AdvancedAI from './components/AdvancedAI';
import { NotificationProvider } from './components/common/NotificationProvider';
import './App.css';
import { apiService } from './services/api';

// Updated User interface to match TemporaryUser model
interface User {
  id: string;
  display_name: string;
  session_code: string;
  role: 'admin' | 'user'; // Add role to user interface
  created_at: string;
}

interface UserContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  loading: boolean;
  showSignIn: boolean;
  handleCreateSession: (displayName: string) => Promise<void>;
  handleLogin: (sessionCode: string) => Promise<void>;
  handleSignOut: () => void;
}

const UserContext = React.createContext<UserContextType | undefined>(undefined);

export const useUser = () => {
  const context = React.useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};

// User Provider Component
const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [showSignIn, setShowSignIn] = useState(false);

  useEffect(() => {
    const loadUserFromSession = async () => {
      const sessionCode = localStorage.getItem('cosenseus_session_code');
      if (sessionCode) {
        try {
          const response = await apiService.loginWithSession(sessionCode);
          // Check for specific error message to clear stale session codes
          if (response.error && response.error.includes('not found')) {
            localStorage.removeItem('cosenseus_session_code');
            setUser(null);
            console.error('Stale session code cleared:', response.error);
          } else if (response.data) {
            setUser(response.data);
          } else if (response.error) {
            console.error('Login failed:', response.error);
          }
        } catch (error) {
          localStorage.removeItem('cosenseus_session_code');
          setUser(null);
          console.error('Failed to load user session:', error);
        }
      }
      setLoading(false);
    };
    loadUserFromSession();
  }, []);

  const handleCreateSession = async (displayName: string) => {
    try {
      const res = await apiService.createSession(displayName);
      if (res.data) {
        localStorage.setItem('cosenseus_session_code', res.data.session_code);
        setUser(res.data);
        setShowSignIn(false);
      }
    } catch (error) {
      console.error('Error creating session:', error);
      // Optionally, handle the error in the UI
    }
  };

  const handleLogin = async (sessionCode: string) => {
    try {
      const res = await apiService.loginWithSession(sessionCode);
      if (res.data) {
        localStorage.setItem('cosenseus_session_code', res.data.session_code);
        setUser(res.data);
        setShowSignIn(false);
      }
    } catch (error) {
      console.error('Error logging in with session:', error);
      // Optionally, handle the error in the UI, e.g., show "Invalid code"
      throw error;
    }
  };

  const handleSignOut = () => {
    localStorage.removeItem('cosenseus_session_code');
    setUser(null);
    setShowSignIn(true);
  };

  return (
    <UserContext.Provider value={{ user, setUser, loading, showSignIn, handleCreateSession, handleLogin, handleSignOut }}>
      {children}
    </UserContext.Provider>
  );
};

// Navigation Component
const Navigation: React.FC = () => {
  const { user, handleSignOut } = useUser();
  const location = useLocation();
  const navigate = useNavigate();
  const [copiedSessionCode, setCopiedSessionCode] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  const copySessionCode = async () => {
    if (!user?.session_code) return;
    
    try {
      await navigator.clipboard.writeText(user.session_code);
      setCopiedSessionCode(true);
      setTimeout(() => setCopiedSessionCode(false), 2000);
    } catch (err) {
      console.error('Failed to copy session code:', err);
    }
  };

  return (
    <nav className="app-navigation">
      <div className="nav-brand">
        <div className="nav-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <Logo size="small" animated={false} />
        </div>
        <h2 onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>CoSenseus</h2>
      </div>
      <div className="nav-links">
        <button 
          className={isActive('/') ? 'btn btn-secondary nav-link active' : 'btn btn-secondary nav-link'}
          onClick={() => navigate('/')}
        >
          Home
        </button>
        <button 
          className={isActive('/events') ? 'btn btn-secondary nav-link active' : 'btn btn-secondary nav-link'}
          onClick={() => navigate('/events')}
        >
          Events
        </button>
      </div>
      <div className="nav-user">
        <span className="user-role">{user ? 'user' : 'anonymous'}</span>
        <span className="user-name">{user?.display_name || 'Anonymous'}</span>
        {user?.session_code && (
          <button 
            className="btn btn-secondary btn-sm session-code-btn"
            onClick={copySessionCode}
            title="Click to copy your session code"
          >
            {copiedSessionCode ? '✓ Copied!' : `📋 ${user.session_code.substring(0, 8)}...`}
          </button>
        )}
        <button className="btn btn-secondary btn-sm" onClick={handleSignOut}>
          Sign Out
        </button>
      </div>
    </nav>
  );
};

// Route Components
const LandingRoute: React.FC = () => {
  const navigate = useNavigate();
  return <LandingPage onGetStarted={() => navigate('/events')} />;
};

const EventsRoute: React.FC = () => {
  const { user } = useUser();
  const navigate = useNavigate();

  const handleEventSelect = (eventId: string, action: 'view' | 'participate' | 'dialogue') => {
    if (action === 'participate') {
      navigate(`/participate/${eventId}`);
    } else if (action === 'view') {
      navigate(`/events/${eventId}`);
    } else if (action === 'dialogue') {
      navigate(`/dialogue/${eventId}`);
    }
  };

  const handleCreateEvent = () => {
    // Navigate to the event creation form
    // This route will need to be created
    navigate('/events/new');
  };

  const handleManageTemplates = () => {
    navigate('/templates');
  };

  return (
    <>
      <Navigation />
      <div className="dashboard-container">
        {user ? (
          <UnifiedDashboard 
            onEventSelect={handleEventSelect} 
            onCreateEvent={handleCreateEvent}
            onManageTemplates={handleManageTemplates}
          />
        ) : (
          <div>Please sign in to see events.</div>
        )}
      </div>
    </>
  );
};

const EventDetailsRoute: React.FC = () => {
  const { eventId } = useParams<{ eventId: string }>();
  const { user } = useUser();
  const navigate = useNavigate();

  if (!eventId) return <Navigate to="/events" />;

  const handleNavigateToParticipate = (eventId: string) => {
    navigate(`/participate/${eventId}`);
  };

  const handleNavigateToResults = (eventId: string) => {
    navigate(`/results/${eventId}`);
  };

  return (
    <>
      <Navigation />
      <div className="dashboard-container">
        <EventDetails
          eventId={eventId}
          userRole={user ? user.role : 'anonymous'}
          onBack={() => navigate('/events')}
          onParticipate={() => navigate(`/participate/${eventId}`)}
          onStartDialogue={() => navigate(`/dialogue/${eventId}`)}
          onNavigateToParticipate={handleNavigateToParticipate}
          onNavigateToResults={handleNavigateToResults}
        />
      </div>
    </>
  );
};

const ParticipateRoute: React.FC = () => {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();

  if (!eventId) return <Navigate to="/events" />;

  return (
    <>
      <Navigation />
      <div className="dashboard-container">
        <DialogueRounds
          eventId={eventId}
          onComplete={() => navigate(`/results/${eventId}`)}
          onBack={() => navigate(`/events/${eventId}`)}
        />
      </div>
    </>
  );
};

const DialogueRoute: React.FC = () => {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();

  if (!eventId) return <Navigate to="/events" />;

  return (
    <>
      <Navigation />
      <div className="dashboard-container">
        <DialogueRounds
          eventId={eventId}
          onComplete={() => {
            alert('Dialogue completed! Thank you for participating.');
            navigate('/events');
          }}
          onBack={() => navigate(`/events/${eventId}`)}
        />
      </div>
    </>
  );
};

const ResultsRoute: React.FC = () => {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();

  if (!eventId) return <Navigate to="/events" />;

  return (
    <>
      <Navigation />
      <div className="dashboard-container">
        <AdvancedAI eventId={eventId} />
      </div>
    </>
  );
};

const CreateEventRoute: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useUser();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (eventData: any) => {
    if (!user) {
      setError("User not found, cannot create event. Please sign in again.");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const payload = { ...eventData, session_code: user.session_code };
      await apiService.createEvent(payload);
      navigate('/events');
    } catch (err) {
      setError('Failed to create event. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Navigation />
      <div className="dashboard-container">
        {error && <div className="error-message">{error}</div>}
        <EventWizard 
          onSubmit={handleSubmit} 
          isLoading={isLoading}
          onCancel={() => navigate('/events')}
        />
      </div>
    </>
  );
};

const TemplateManagerRoute: React.FC = () => {
  const navigate = useNavigate();
  return (
    <>
      <Navigation />
      <div className="dashboard-container">
        <TemplateManager onBack={() => navigate('/events')} />
      </div>
    </>
  );
};

// Loading Component
const LoadingScreen: React.FC = () => (
  <div className="loading-screen">
    <Logo size="large" animated={true} />
    <p>Loading Your Experience...</p>
  </div>
);

// Main App Component
function App() {
  return (
    <NotificationProvider>
      <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <UserProvider>
          <AppContent />
        </UserProvider>
      </Router>
    </NotificationProvider>
  );
}

const AppContent: React.FC = () => {
  const { user, loading, showSignIn, handleCreateSession, handleLogin } = useUser();
  const location = useLocation();
  const navigate = useNavigate();

  // Redirect authenticated users to dashboard if they're not on a valid route
  useEffect(() => {
    if (user && !loading) {
      // Define routes that are safe to stay on after authentication
      const safeRoutes = ['/', '/events', '/events/new', '/templates'];
      const isOnEventRoute = location.pathname.startsWith('/events/') && location.pathname !== '/events/new';
      const isOnParticipateRoute = location.pathname.startsWith('/participate/');
      const isOnDialogueRoute = location.pathname.startsWith('/dialogue/');
      const isOnResultsRoute = location.pathname.startsWith('/results/');
      
      // If user is on a specific event-related route, let them stay
      // Otherwise, redirect to dashboard
      if (!safeRoutes.includes(location.pathname) && 
          !isOnEventRoute && 
          !isOnParticipateRoute && 
          !isOnDialogueRoute && 
          !isOnResultsRoute) {
        navigate('/events');
      }
    }
  }, [user, loading, location.pathname, navigate]);

  if (loading) {
    return <LoadingScreen />;
  }

  if (showSignIn || !user) {
    return <SignIn onCreateSession={handleCreateSession} onLogin={handleLogin} onBack={() => {}} />;
  }

  return (
    <Routes>
      <Route path="/" element={<LandingRoute />} />
      <Route path="/events" element={<EventsRoute />} />
      <Route path="/events/new" element={<CreateEventRoute />} />
      <Route path="/events/:eventId" element={<EventDetailsRoute />} />
      <Route path="/participate/:eventId" element={<ParticipateRoute />} />
      <Route path="/dialogue/:eventId" element={<DialogueRoute />} />
      <Route path="/results/:eventId" element={<ResultsRoute />} />
      <Route path="/templates" element={<TemplateManagerRoute />} />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
};

const DialogueRoundsWrapper: React.FC = () => {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();
  if (!eventId) {
    return <p>Event not found.</p>;
  }
  return <DialogueRounds eventId={eventId} onBack={() => navigate('/')} onComplete={() => navigate(`/results/${eventId}`)} />;
};

export default App; 