import React, { useState, useCallback } from 'react';
import './EventWizard.css';

interface Inquiry {
  title: string;
  content: string;
  inquiry_type: string;
  required: boolean;
  order_index: number;
}

interface EventFormData {
  title: string;
  description: string;
  event_type: string;
  max_participants?: number;
  registration_deadline?: string;
  start_time?: string;
  end_time?: string;
  is_public: boolean;
  allow_anonymous: boolean;
  inquiries: Inquiry[];
}

interface EventWizardProps {
  onSubmit: (eventData: EventFormData) => void;
  isLoading?: boolean;
  onCancel?: () => void;
  initialData?: EventFormData;
}

const EventWizard: React.FC<EventWizardProps> = ({ onSubmit, isLoading = false, onCancel, initialData }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<EventFormData>(
    initialData ? { ...initialData } : {
      title: '',
      description: '',
      event_type: 'discussion',
      is_public: true,
      allow_anonymous: false,
      inquiries: []
    }
  );
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Update formData if initialData changes (for editing)
  React.useEffect(() => {
    if (initialData) {
      setFormData({ ...initialData });
    }
  }, [initialData]);

  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {};

    if (step === 1) {
      if (!formData.title.trim()) {
        newErrors.title = 'Event title is required';
      } else if (formData.title.length > 200) {
        newErrors.title = 'Title must be 200 characters or less';
      }

      if (!formData.description.trim()) {
        newErrors.description = 'Event description is required';
      } else if (formData.description.length > 5000) {
        newErrors.description = 'Description must be 5000 characters or less';
      }

      if (formData.max_participants && formData.max_participants < 1) {
        newErrors.max_participants = 'Maximum participants must be at least 1';
      }
    }

    if (step === 2) {
      if (formData.start_time && formData.end_time) {
        const startDate = new Date(formData.start_time);
        const endDate = new Date(formData.end_time);
        if (startDate >= endDate) {
          newErrors.end_time = 'End time must be after start time';
        }
      }

      if (formData.registration_deadline && formData.start_time) {
        const regDate = new Date(formData.registration_deadline);
        const startDate = new Date(formData.start_time);
        if (regDate >= startDate) {
          newErrors.registration_deadline = 'Registration deadline must be before start time';
        }
      }
    }

    if (step === 3) {
      formData.inquiries.forEach((inquiry, index) => {
        if (!inquiry.title.trim()) {
          newErrors[`inquiry_${index}_title`] = `Inquiry ${index + 1} title is required`;
        }
        if (!inquiry.content.trim()) {
          newErrors[`inquiry_${index}_content`] = `Inquiry ${index + 1} content is required`;
        }
      });
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 3));
    }
  };

  const handlePrev = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleInputChange = (field: keyof EventFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleInquiryChange = (index: number, field: keyof Inquiry, value: any) => {
    const newInquiries = [...formData.inquiries];
    newInquiries[index] = { ...newInquiries[index], [field]: value };
    setFormData(prev => ({ ...prev, inquiries: newInquiries }));
    
    // Clear error when user starts typing
    const errorKey = `inquiry_${index}_${field}`;
    if (errors[errorKey]) {
      setErrors(prev => ({ ...prev, [errorKey]: '' }));
    }
  };

  const addInquiry = () => {
    const newInquiry: Inquiry = {
      title: '',
      content: '',
      inquiry_type: 'open_ended',
      required: true,
      order_index: formData.inquiries.length
    };
    setFormData(prev => ({
      ...prev,
      inquiries: [...prev.inquiries, newInquiry]
    }));
  };

  const removeInquiry = (index: number) => {
    const newInquiries = formData.inquiries.filter((_, i) => i !== index);
    // Update order numbers
    const reorderedInquiries = newInquiries.map((inquiry, i) => ({
      ...inquiry,
      order_index: i
    }));
    setFormData(prev => ({ ...prev, inquiries: reorderedInquiries }));
  };

  const moveInquiry = (index: number, direction: 'up' | 'down') => {
    const newInquiries = [...formData.inquiries];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (targetIndex >= 0 && targetIndex < newInquiries.length) {
      [newInquiries[index], newInquiries[targetIndex]] = 
      [newInquiries[targetIndex], newInquiries[index]];
      
      // Update order numbers
      newInquiries.forEach((inquiry, i) => {
        inquiry.order_index = i;
      });
      
      setFormData(prev => ({ ...prev, inquiries: newInquiries }));
    }
  };

  const handleSubmit = () => {
    if (validateStep(3)) {
      // If no inquiries have been added, add a default one.
      if (formData.inquiries.length === 0) {
        const dataWithDefaultInquiry = {
          ...formData,
          inquiries: [
            {
              title: 'General Feedback',
              content: 'What are your general thoughts or feedback on the topic of this event?',
              inquiry_type: 'open_ended',
              required: true,
              order_index: 0,
            },
          ],
        };
        onSubmit(dataWithDefaultInquiry);
        return;
      }
      onSubmit(formData);
    }
  };

  const renderStep1 = () => (
    <div className="step-content">
      <h3>Basic Information</h3>
      
      <div className="form-group">
        <label htmlFor="title">Event Title *</label>
        <input
          type="text"
          id="title"
          value={formData.title}
          onChange={(e) => handleInputChange('title', e.target.value)}
          className={errors.title ? 'error' : ''}
          placeholder="Enter event title"
          maxLength={200}
        />
        {errors.title && <span className="error-text">{errors.title}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="description">Description *</label>
        <textarea
          id="description"
          value={formData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          className={errors.description ? 'error' : ''}
          placeholder="Describe your event and its purpose"
          rows={4}
          maxLength={5000}
        />
        {errors.description && <span className="error-text">{errors.description}</span>}
        <small>{formData.description.length}/5000 characters</small>
      </div>

      <div className="form-group">
        <label htmlFor="event_type">Event Type</label>
        <select
          id="event_type"
          value={formData.event_type}
          onChange={(e) => handleInputChange('event_type', e.target.value)}
        >
          <option value="discussion">Discussion</option>
          <option value="consultation">Consultation</option>
          <option value="planning">Planning Session</option>
          <option value="feedback">Feedback Collection</option>
          <option value="other">Other</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="max_participants">Maximum Participants</label>
        <input
          type="number"
          id="max_participants"
          value={formData.max_participants || ''}
          onChange={(e) => handleInputChange('max_participants', e.target.value ? parseInt(e.target.value) : undefined)}
          className={errors.max_participants ? 'error' : ''}
          placeholder="Leave empty for unlimited"
          min="1"
        />
        {errors.max_participants && <span className="error-text">{errors.max_participants}</span>}
      </div>

      <div className="form-group checkbox-group">
        <label>
          <input
            type="checkbox"
            checked={formData.is_public}
            onChange={(e) => handleInputChange('is_public', e.target.checked)}
          />
          <span>Make this event public</span>
        </label>
        <small>Public events are visible to all users</small>
      </div>

      <div className="form-group checkbox-group">
        <label>
          <input
            type="checkbox"
            checked={formData.allow_anonymous}
            onChange={(e) => handleInputChange('allow_anonymous', e.target.checked)}
          />
          <span>Allow anonymous participation</span>
        </label>
        <small>Participants can choose to participate anonymously</small>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="step-content">
      <h3>Schedule & Timing</h3>
      
      <div className="form-group">
        <label htmlFor="start_time">Start Time</label>
        <input
          type="datetime-local"
          id="start_time"
          value={formData.start_time || ''}
          onChange={(e) => handleInputChange('start_time', e.target.value)}
          className={errors.start_time ? 'error' : ''}
        />
        {errors.start_time && <span className="error-text">{errors.start_time}</span>}
        <small>Leave empty if this event doesn't have a specific start time</small>
      </div>

      <div className="form-group">
        <label htmlFor="end_time">End Time</label>
        <input
          type="datetime-local"
          id="end_time"
          value={formData.end_time || ''}
          onChange={(e) => handleInputChange('end_time', e.target.value)}
          className={errors.end_time ? 'error' : ''}
        />
        {errors.end_time && <span className="error-text">{errors.end_time}</span>}
        <small>Leave empty if this event doesn't have a specific end time</small>
      </div>

      <div className="form-group">
        <label htmlFor="registration_deadline">Registration Deadline</label>
        <input
          type="datetime-local"
          id="registration_deadline"
          value={formData.registration_deadline || ''}
          onChange={(e) => handleInputChange('registration_deadline', e.target.value)}
          className={errors.registration_deadline ? 'error' : ''}
        />
        {errors.registration_deadline && <span className="error-text">{errors.registration_deadline}</span>}
        <small>Leave empty if registration never closes</small>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="step-content">
      <h3>Event Inquiries</h3>
      <p>Create questions or prompts for participants to respond to:</p>
      
      {errors.inquiries && <div className="error-text">{errors.inquiries}</div>}
      
      {formData.inquiries.map((inquiry, index) => (
        <div key={index} className="inquiry-item">
          <div className="inquiry-header">
            <h4>Inquiry {index + 1}</h4>
            <div className="inquiry-controls">
              <button
                type="button"
                onClick={() => moveInquiry(index, 'up')}
                disabled={index === 0}
                className="move-btn"
              >
                ↑
              </button>
              <button
                type="button"
                onClick={() => moveInquiry(index, 'down')}
                disabled={index === formData.inquiries.length - 1}
                className="move-btn"
              >
                ↓
              </button>
              <button
                type="button"
                onClick={() => removeInquiry(index)}
                className="remove-btn"
              >
                Remove
              </button>
            </div>
          </div>
          
          <div className="form-group">
            <label>Inquiry Title *</label>
            <input
              type="text"
              value={inquiry.title}
              onChange={(e) => handleInquiryChange(index, 'title', e.target.value)}
              className={errors[`inquiry_${index}_title`] ? 'error' : ''}
              placeholder="Brief title for this inquiry"
              maxLength={500}
            />
            {errors[`inquiry_${index}_title`] && 
              <span className="error-text">{errors[`inquiry_${index}_title`]}</span>
            }
          </div>
          
          <div className="form-group">
            <label>Question/Prompt *</label>
            <textarea
              value={inquiry.content}
              onChange={(e) => handleInquiryChange(index, 'content', e.target.value)}
              className={errors[`inquiry_${index}_content`] ? 'error' : ''}
              placeholder="What would you like participants to discuss or respond to?"
              rows={3}
              maxLength={10000}
            />
            {errors[`inquiry_${index}_content`] && 
              <span className="error-text">{errors[`inquiry_${index}_content`]}</span>
            }
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label>Type</label>
              <select
                value={inquiry.inquiry_type}
                onChange={(e) => handleInquiryChange(index, 'inquiry_type', e.target.value)}
              >
                <option value="open_ended">Open-ended</option>
                <option value="structured">Structured</option>
                <option value="multiple_choice">Multiple Choice</option>
              </select>
            </div>
            
            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={inquiry.required}
                  onChange={(e) => handleInquiryChange(index, 'required', e.target.checked)}
                />
                <span>Required</span>
              </label>
            </div>
          </div>
        </div>
      ))}
      
      <button
        type="button"
        onClick={addInquiry}
        className="add-inquiry-btn"
      >
        + Add Inquiry
      </button>
    </div>
  );

  return (
    <div className="event-wizard">
      <div className="wizard-header">
        <h2>Create New Event</h2>
        <div className="step-indicator">
          <div className={`step ${currentStep >= 1 ? 'active' : ''}`}>1</div>
          <div className={`step ${currentStep >= 2 ? 'active' : ''}`}>2</div>
          <div className={`step ${currentStep >= 3 ? 'active' : ''}`}>3</div>
        </div>
      </div>

      <div className="wizard-content">
        {currentStep === 1 && renderStep1()}
        {currentStep === 2 && renderStep2()}
        {currentStep === 3 && renderStep3()}
      </div>

      <div className="wizard-footer">
        <div className="button-group">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="btn-secondary"
              disabled={isLoading}
            >
              Cancel
            </button>
          )}
          
          {currentStep > 1 && (
            <button
              type="button"
              onClick={handlePrev}
              className="btn-secondary"
              disabled={isLoading}
            >
              Previous
            </button>
          )}
          
          {currentStep < 3 ? (
            <button
              type="button"
              onClick={handleNext}
              className="btn-primary"
              disabled={isLoading}
            >
              Next
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              className="btn-primary"
              disabled={isLoading}
            >
              {isLoading ? 'Creating...' : 'Create Event'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default EventWizard; 