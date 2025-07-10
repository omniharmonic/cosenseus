import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import './UnifiedDashboard.css';

// Define the shape of the event summary data
interface EventSummary {
  id: string;
  title: string;
  description: string;
  status: string;
  created_at: string;
}

// Define the props for the dashboard
interface UnifiedDashboardProps {
  onEventSelect: (eventId: string, action: 'view' | 'participate' | 'dialogue') => void;
  onCreateEvent: () => void;
  onManageTemplates: () => void;
}

const UnifiedDashboard: React.FC<UnifiedDashboardProps> = ({ onEventSelect, onCreateEvent, onManageTemplates }) => {
  const [organizedEvents, setOrganizedEvents] = useState<EventSummary[]>([]);
  const [participatingEvents, setParticipatingEvents] = useState<EventSummary[]>([]);
  const [activeTab, setActiveTab] = useState<'admin' | 'participant'>('admin');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const response = await apiService.getDashboardEvents();
        if (response.data) {
          setOrganizedEvents(response.data.organized_events || []);
          setParticipatingEvents(response.data.participating_events || []);
        } else {
          setError(response.error || 'Failed to fetch dashboard data.');
        }
      } catch (err) {
        setError('An unexpected error occurred.');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const handleDelete = async (eventId: string) => {
    if (window.confirm('Are you sure you want to permanently delete this event?')) {
      try {
        const response = await apiService.deleteEvent(eventId);
        if (response.error) {
          setError(response.error);
        } else {
          setOrganizedEvents(organizedEvents.filter(event => event.id !== eventId));
        }
      } catch (err) {
        setError('An unexpected error occurred while deleting the event.');
      }
    }
  };

  const renderEventList = (events: EventSummary[], isOrganizer: boolean) => {
    if (events.length === 0) {
      return <p>No events to display.</p>;
    }

    return (
      <div className="event-list">
        {events.map((event) => (
          <div key={event.id} className="event-card">
            <h3>{event.title}</h3>
            <p>{event.description}</p>
            <div className="event-footer">
              <span>Status: {event.status}</span>
              <span>Created: {new Date(event.created_at).toLocaleDateString()}</span>
              <div className="event-actions">
                {isOrganizer ? (
                  <>
                    <button className="btn btn-secondary" onClick={() => onEventSelect(event.id, 'view')}>Manage</button>
                    <button onClick={() => handleDelete(event.id)} className="btn btn-danger">Delete</button>
                  </>
                ) : (
                  <button className="btn btn-primary" onClick={() => onEventSelect(event.id, 'participate')}>Join</button>
                )}
                <button className="btn btn-secondary" onClick={() => onEventSelect(event.id, 'dialogue')}>View Results</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return <div>Loading dashboard...</div>;
  }

  if (error) {
    return <div className="error-message">Error: {error}</div>;
  }

  return (
    <div className="unified-dashboard">
      <h2>Your Dashboard</h2>
      <div className="dashboard-tabs">
        <button 
          className={`btn ${activeTab === 'admin' ? 'active' : ''}`}
          onClick={() => setActiveTab('admin')}
        >
          Organizing ({organizedEvents.length})
        </button>
        <button
          className={`btn ${activeTab === 'participant' ? 'active' : ''}`}
          onClick={() => setActiveTab('participant')}
        >
          Participating ({participatingEvents.length})
        </button>
      </div>
      <div className="dashboard-content">
        {activeTab === 'admin' && (
          <div className="admin-header">
            <button className="btn btn-secondary" onClick={onManageTemplates}>
              Manage Templates
            </button>
            <button className="btn btn-primary" onClick={onCreateEvent}>
              + Create New Event
            </button>
          </div>
        )}
        {activeTab === 'admin' ? (
          renderEventList(organizedEvents, true)
        ) : (
          renderEventList(participatingEvents, false)
        )}
      </div>
    </div>
  );
};

export default UnifiedDashboard; 