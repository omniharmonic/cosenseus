import React, { useState, useEffect } from 'react';
import { apiService, EventTemplate } from '../services/api';
import TemplateEditor from './TemplateEditor';
import LoadingSpinner from './common/LoadingSpinner';
import EmptyState from './common/EmptyState';
import { useNotification } from './common/NotificationProvider';
import './TemplateManager.css';

interface TemplateManagerProps {
  onBack: () => void;
}

const TemplateManager: React.FC<TemplateManagerProps> = ({ onBack }) => {
  const [eventTemplates, setEventTemplates] = useState<EventTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<EventTemplate | null>(null);
  const { showNotification } = useNotification();

  const fetchEventTemplates = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getEventTemplates();
      if (response.data) {
        setEventTemplates(response.data);
      } else if (response.error) {
        showNotification(response.error, 'error');
      }
    } catch (err) {
      showNotification('Failed to fetch event templates.', 'error');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEventTemplates();
  }, []);

  const handleCreateNew = () => {
    setEditingTemplate(null);
    setIsEditorOpen(true);
  };

  const handleEdit = (template: EventTemplate) => {
    setEditingTemplate(template);
    setIsEditorOpen(true);
  };

  const handleSave = async (templateData: any) => {
    try {
      if (editingTemplate) {
        await apiService.updateEventTemplate(editingTemplate.id, templateData);
        showNotification('Template updated successfully!', 'success');
      } else {
        await apiService.createEventTemplate(templateData);
        showNotification('Template created successfully!', 'success');
      }
      setIsEditorOpen(false);
      fetchEventTemplates(); // Refresh the list
    } catch (err) {
      showNotification('Failed to save template.', 'error');
      console.error(err);
    }
  };

  const handleDelete = async (templateId: string) => {
    if (window.confirm('Are you sure you want to delete this template?')) {
      try {
        await apiService.deleteEventTemplate(templateId);
        showNotification('Template deleted successfully.', 'success');
        fetchEventTemplates();
      } catch (err) {
        showNotification('Failed to delete template.', 'error');
        console.error(err);
      }
    }
  };

  if (isLoading && !isEditorOpen) {
    return (
      <div className="template-manager">
        <LoadingSpinner message="Loading templates..." />
      </div>
    );
  }

  return (
    <div className="template-manager">
      <div className="tm-header">
        <button className="btn btn-secondary" onClick={onBack}>
          &larr; Back to Dashboard
        </button>
        <h2>Event Template Management</h2>
        <button className="btn btn-primary" onClick={handleCreateNew}>
          + Create New Template
        </button>
      </div>

      {eventTemplates.length > 0 ? (
        <div className="tm-list">
          {eventTemplates.map(template => (
            <div key={template.id} className="tm-card">
              <div className="tm-card-content">
                <h4>{template.name}</h4>
                <p>{template.description}</p>
              </div>
              <div className="tm-card-actions">
                <button className="btn btn-secondary" onClick={() => handleEdit(template)}>Edit</button>
                <button className="btn btn-danger" onClick={() => handleDelete(template.id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState 
          title="No Event Templates Found"
          message="Get started by creating your first event template."
          action={{ text: '+ Create New Template', onClick: handleCreateNew }}
        />
      )}


      {isEditorOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <TemplateEditor
              template={editingTemplate}
              onSave={handleSave}
              onCancel={() => setIsEditorOpen(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateManager; 