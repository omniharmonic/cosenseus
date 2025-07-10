import React, { useState, useEffect } from 'react';
import EventWizard from './EventWizard';
import { apiService } from '../services/api';
import './EventDashboard.css';

interface Event {
  id: string;
  title: string;
  description: string;
  event_type: string;
  status: string;
  current_participants: number;
  max_participants?: number;
  start_time?: string;
  is_public: boolean;
  created_at: string;
}

interface EventDashboardProps {
  userRole?: 'admin' | 'user' | 'anonymous';
  onEventSelect?: (eventId: string, action: 'view' | 'participate') => void;
}

const EventDashboard: React.FC<EventDashboardProps> = ({ 
  userRole = 'user',
  onEventSelect 
}) => {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateWizard, setShowCreateWizard] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [copiedLink, setCopiedLink] = useState<'participate' | 'results' | null>(null);
  const [editingEvent, setEditingEvent] = useState<Event | null>(null);
  const [editingEventFormData, setEditingEventFormData] = useState<any | null>(null);

  // Add migration logic at the top of the file (after imports)
  const oldSessionCode = localStorage.getItem('census_session_code');
  if (oldSessionCode && !localStorage.getItem('cosenseus_session_code')) {
    localStorage.setItem('cosenseus_session_code', oldSessionCode);
  }

  // Real API functions
  const fetchEvents = async () => {
    setLoading(true);
    try {
      const response = await apiService.getEvents();
      
      if (response.error) {
        setError(response.error);
        return;
      }
      
      setEvents(response.data || []);
      setError(null);
    } catch (err) {
      setError('Failed to load events');
      console.error('Error fetching events:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEvent = async (eventData: any) => {
    try {
      setLoading(true);

      const sessionCode = localStorage.getItem('cosenseus_session_code');
      if (!sessionCode) {
        setError("You must be logged in to create an event.");
        setLoading(false);
        return;
      }

      const payload = { ...eventData, session_code: sessionCode };
      const response = await apiService.createEvent(payload);
      
      if (response.error) {
        setError(response.error);
        return;
      }
      
      // Refresh events list
      await fetchEvents();
      setShowCreateWizard(false);
      setError(null);
    } catch (err) {
      setError('Failed to create event');
      console.error('Error creating event:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleEditButtonClick = async (event: Event) => {
    try {
      setLoading(true);
      const response = await apiService.getEvent(event.id);
      if (response.error || !response.data) {
        setError(response.error || 'Failed to fetch event details');
        return;
      }
      // Map API response to EventFormData
      const data = response.data;
      const formData = {
        title: data.title,
        description: data.description,
        event_type: data.event_type,
        max_participants: data.max_participants,
        registration_deadline: data.registration_deadline,
        start_time: data.start_time,
        end_time: data.end_time,
        is_public: data.is_public,
        allow_anonymous: data.allow_anonymous,
        inquiries: (data.inquiries || []).map((inq: any, i: number) => ({
          title: inq.title,
          content: inq.content,
          inquiry_type: inq.inquiry_type,
          required: inq.required,
          order: typeof inq.order_index === 'number' ? inq.order_index : i
        }))
      };
      setEditingEventFormData({ ...formData, id: event.id });
    } catch (err) {
      setError('Failed to load event for editing');
    } finally {
      setLoading(false);
    }
  };

  const handleEditEvent = async (eventData: any) => {
    if (!editingEvent) return;
    try {
      setLoading(true);
      const response = await apiService.updateEvent(editingEvent.id, eventData);
      if (response.error) {
        setError(response.error);
        return;
      }
      setEditingEvent(null);
      await fetchEvents();
    } catch (err) {
      setError('Failed to update event');
    } finally {
      setLoading(false);
    }
  };

  const handlePublishEvent = async (eventId: string) => {
    try {
      const response = await apiService.publishEvent(eventId);
      if (response.error) {
        setError(response.error);
        return;
      }
      // Refresh events list
      await fetchEvents();
    } catch (err: any) {
      setError(err?.message || 'Failed to publish event');
      console.error('Error publishing event:', err);
    }
  };

  const handleDeleteEvent = async (eventId: string) => {
    if (!confirm('Are you sure you want to delete this event?')) {
      return;
    }
    
    try {
      const response = await apiService.deleteEvent(eventId);
      
      if (response.error) {
        setError(response.error);
        return;
      }
      
      // Refresh events list
      await fetchEvents();
    } catch (err) {
      setError('Failed to delete event');
      console.error('Error deleting event:', err);
    }
  };

  // Handle event button clicks
  const handleViewDetails = (eventId: string) => {
    console.log('Viewing details for event:', eventId);
    if (onEventSelect) {
      onEventSelect(eventId, 'view');
    }
  };

  const handleParticipate = (eventId: string) => {
    console.log('Participating in event:', eventId);
    if (onEventSelect) {
      onEventSelect(eventId, 'participate');
    }
  };

  const copyToClipboard = async (text: string, type: 'participate' | 'results') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedLink(type);
      setTimeout(() => setCopiedLink(null), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  const getParticipateLink = (eventId: string) => {
    const baseUrl = window.location.origin;
    return `${baseUrl}/participate/${eventId}`;
  };

  const getResultsLink = (eventId: string) => {
    const baseUrl = window.location.origin;
    return `${baseUrl}/results/${eventId}`;
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  // Filter events based on current filters
  const filteredEvents = events.filter(event => {
    const matchesStatus = filterStatus === 'all' || event.status === filterStatus;
    const matchesType = filterType === 'all' || event.event_type === filterType;
    const matchesSearch = searchTerm === '' || 
      event.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      event.description.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesStatus && matchesType && matchesSearch;
  });

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'active': return 'status-badge active';
      case 'draft': return 'status-badge draft';
      case 'completed': return 'status-badge completed';
      case 'cancelled': return 'status-badge cancelled';
      default: return 'status-badge';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (showCreateWizard) {
    return (
      <div className="dashboard-container">
        <EventWizard
          onSubmit={handleCreateEvent}
          isLoading={loading}
          onCancel={() => setShowCreateWizard(false)}
        />
      </div>
    );
  }

  if (editingEventFormData) {
    return (
      <div className="dashboard-container">
        <EventWizard
          initialData={editingEventFormData}
          onSubmit={async (eventData) => {
            try {
              setLoading(true);
              const response = await apiService.updateEvent(editingEventFormData.id, eventData);
              if (response.error) {
                setError(response.error);
                return;
              }
              setEditingEventFormData(null);
              await fetchEvents();
            } catch (err) {
              setError('Failed to update event');
            } finally {
              setLoading(false);
            }
          }}
          isLoading={loading}
          onCancel={() => setEditingEventFormData(null)}
        />
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div className="header-content">
          <h1>Event Dashboard</h1>
          <p>Manage and monitor your civic engagement events</p>
        </div>
        
        {userRole !== 'anonymous' && (
          <button
            className="btn-primary create-event-btn"
            onClick={() => setShowCreateWizard(true)}
          >
            + Create Event
          </button>
        )}
      </div>

      {error && (
        <div className="error-banner">
          <p>{error}</p>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      <div className="dashboard-controls">
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search events..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="filters">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="all">All Status</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="all">All Types</option>
            <option value="discussion">Discussion</option>
            <option value="consultation">Consultation</option>
            <option value="planning">Planning</option>
            <option value="feedback">Feedback</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      <div className="events-grid">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading events...</p>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="empty-state">
            <h3>No events found</h3>
            <p>
              {events.length === 0 
                ? "You haven't created any events yet."
                : "No events match your current filters."
              }
            </p>
            {userRole !== 'anonymous' && events.length === 0 && (
              <button
                className="btn-primary"
                onClick={() => setShowCreateWizard(true)}
              >
                Create Your First Event
              </button>
            )}
          </div>
        ) : (
          filteredEvents.map(event => (
            <div key={event.id} className="event-card">
              <div className="event-header">
                <div className="event-meta">
                  <span className={getStatusBadgeClass(event.status)}>
                    {event.status}
                  </span>
                  <span className="event-type">{event.event_type}</span>
                </div>
                
                {userRole === 'admin' && (
                  <div className="event-actions">
                    {event.status === 'draft' && (
                      <button
                        className="action-btn publish"
                        onClick={() => handlePublishEvent(event.id)}
                        title="Publish Event"
                      >
                        📢
                      </button>
                    )}
                    <button
                      className="action-btn edit"
                      onClick={() => handleEditButtonClick(event)}
                      title="Edit Event"
                    >
                      ✏️
                    </button>
                    <button
                      className="action-btn delete"
                      onClick={() => handleDeleteEvent(event.id)}
                      title="Delete Event"
                    >
                      🗑️
                    </button>
                  </div>
                )}
              </div>
              
              <div className="event-content">
                <h3>{event.title}</h3>
                <p>{event.description}</p>
                
                <div className="event-details">
                  <div className="detail-item">
                    <span className="label">Participants:</span>
                    <span className="value">
                      {event.current_participants}
                      {event.max_participants && ` / ${event.max_participants}`}
                    </span>
                  </div>
                  
                  {event.start_time && (
                    <div className="detail-item">
                      <span className="label">Start Time:</span>
                      <span className="value">{formatDate(event.start_time)}</span>
                    </div>
                  )}
                  
                  <div className="detail-item">
                    <span className="label">Created:</span>
                    <span className="value">{formatDate(event.created_at)}</span>
                  </div>
                  
                  <div className="detail-item">
                    <span className="label">Visibility:</span>
                    <span className="value">{event.is_public ? 'Public' : 'Private'}</span>
                  </div>
                </div>
              </div>
              
              <div className="event-footer">
                <div className="event-actions-main">
                  <button
                    className="btn-secondary view-btn"
                    onClick={() => handleViewDetails(event.id)}
                  >
                    View Details
                  </button>
                  
                  {event.status === 'active' && (
                    <button
                      className="btn-primary participate-btn"
                      onClick={() => handleParticipate(event.id)}
                    >
                      {userRole === 'anonymous' ? 'Join Event' : 'Participate'}
                    </button>
                  )}
                </div>
                
                <div className="event-share-links">
                  <div className="share-label">Shareable Links:</div>
                  <div className="share-links-list">
                    <div className="share-link-row">
                      <span className="share-link-type">Participate:</span>
                      <input
                        className="share-link-input"
                        value={getParticipateLink(event.id)}
                        readOnly
                        onFocus={e => e.target.select()}
                      />
                      <button
                        className="link-btn"
                        onClick={() => copyToClipboard(getParticipateLink(event.id), 'participate')}
                        title="Copy participate link"
                      >
                        {copiedLink === 'participate' ? '✓' : '📋'}
                      </button>
                    </div>
                    <div className="share-link-row">
                      <span className="share-link-type">Results:</span>
                      <input
                        className="share-link-input"
                        value={getResultsLink(event.id)}
                        readOnly
                        onFocus={e => e.target.select()}
                      />
                      <button
                        className="link-btn"
                        onClick={() => copyToClipboard(getResultsLink(event.id), 'results')}
                        title="Copy results link"
                      >
                        {copiedLink === 'results' ? '✓' : '📋'}
                      </button>
                    </div>
                  </div>
                  {copiedLink && <div className="copy-confirm">Link copied!</div>}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
      
      {filteredEvents.length > 0 && (
        <div className="dashboard-stats">
          <div className="stat-item">
            <span className="stat-value">{events.length}</span>
            <span className="stat-label">Total Events</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">
              {events.filter(e => e.status === 'active').length}
            </span>
            <span className="stat-label">Active Events</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">
              {events.reduce((sum, e) => sum + e.current_participants, 0)}
            </span>
            <span className="stat-label">Total Participants</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default EventDashboard; 