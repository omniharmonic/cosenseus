import React, { useState } from 'react';
import { EventTemplate } from '../services/api';
import EventWizard from './EventWizard';
import './TemplateEditor.css';

interface TemplateEditorProps {
  template?: EventTemplate | null;
  onSave: (templateData: any) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const TemplateEditor: React.FC<TemplateEditorProps> = ({ template, onSave, onCancel, isLoading }) => {
  const [name, setName] = useState(template?.name || '');
  const [description, setDescription] = useState(template?.description || '');
  
  // The structure is managed by the EventWizard
  const handleWizardSubmit = (structure: any) => {
    onSave({
      name,
      description,
      structure,
    });
  };

  return (
    <div className="template-editor">
      <h3>{template ? 'Edit' : 'Create'} Event Template</h3>
      <div className="form-group">
        <label htmlFor="template-name">Template Name *</label>
        <input
          id="template-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., Standard Community Consultation"
        />
      </div>
      <div className="form-group">
        <label htmlFor="template-description">Description</label>
        <textarea
          id="template-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          placeholder="A brief description of when to use this template."
        />
      </div>
      <hr />
      <h4>Template Content</h4>
      <p>Use the wizard below to define the inquiries and settings for this template.</p>
      
      <div className="wizard-container">
        <EventWizard 
          // The wizard's submit button will trigger our save handler
          onSubmit={handleWizardSubmit} 
          // Pass the existing structure if we are editing
          initialData={template?.event_data}
          // We can customize the wizard's buttons or behavior if needed
          isLoading={isLoading}
        />
      </div>

      {/* The actual save/cancel buttons are part of the EventWizard now */}
      {/* We can add a top-level cancel if needed */}
      <button onClick={onCancel} className="btn-secondary" style={{marginTop: '20px'}}>
        Cancel
      </button>
    </div>
  );
};

export default TemplateEditor; 