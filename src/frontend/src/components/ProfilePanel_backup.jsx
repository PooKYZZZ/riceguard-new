import React, { useState, useRef, useEffect } from 'react';
import { tokenStorage } from '../secureStorage';
import { updateUserProfile } from '../api';
import './ProfilePanel.css';

const ProfilePanel = ({ isOpen, onClose, user }) => {
  const [isEditMode, setIsEditMode] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    bio: ''
  });
  const [originalData, setOriginalData] = useState({});
  const [avatarPreview, setAvatarPreview] = useState(null);
  const [avatarFile, setAvatarFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  // Initialize form data when user prop changes
  useEffect(() => {
    if (user) {
      const userData = {
        name: user.name || '',
        email: user.email || '',
        bio: user.bio || ''
      };
      setFormData(userData);
      setOriginalData(userData);
      setAvatarPreview(user.avatar || null);
    }
  }, [user]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleEditToggle = () => {
    if (isEditMode) {
      // Cancel editing - restore original data
      setFormData(originalData);
      setAvatarPreview(user.avatar || null);
      setAvatarFile(null);
      setError('');
    }
    setIsEditMode(!isEditMode);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleAvatarFile(files[0]);
    }
  };

  const handleAvatarClick = () => {
    if (isEditMode) {
      fileInputRef.current?.click();
    }
  };

  const handleAvatarFile = (file) => {
    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file (JPEG, PNG, etc.)');
      return;
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      setError('File size must be less than 5MB');
      return;
    }

    setError('');
    setAvatarFile(file);

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setAvatarPreview(e.target.result);
    };
    reader.readAsDataURL(file);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleAvatarFile(file);
    }
  };

  const validateForm = () => {
    if (!formData.name.trim()) {
      setError('Name is required');
      return false;
    }

    if (formData.name.length > 50) {
      setError('Name must be less than 50 characters');
      return false;
    }

    if (formData.bio && formData.bio.length > 200) {
      setError('Bio must be less than 200 characters');
      return false;
    }

    return true;
  };

  const handleSave = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    setError('');

    try {
      // Create FormData for file upload
      const updateData = new FormData();
      updateData.append('name', formData.name.trim());
      updateData.append('email', formData.email);

      if (formData.bio !== undefined) {
        updateData.append('bio', formData.bio.trim());
      }

      if (avatarFile) {
        updateData.append('avatar', avatarFile);
      }

      // Use the new API function
      const updatedUser = await updateUserProfile(updateData);

      // Update stored user data
      const currentUser = tokenStorage.getUser() || {};
      const newUserData = { ...currentUser, ...updatedUser };
      tokenStorage.setToken(tokenStorage.getValidatedToken(), newUserData);

      // Update local state
      setOriginalData({
        name: updatedUser.name,
        email: updatedUser.email,
        bio: updatedUser.bio || ''
      });

      setIsEditMode(false);
      setAvatarFile(null);

    } catch (err) {
      setError(err.message || 'Failed to update profile');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="profile-panel-overlay" role="dialog" aria-modal="true" aria-labelledby="profile-title">
      <div className="profile-panel-modal">
        {/* Header */}
        <header className="profile-panel-header">
          <h2 id="profile-title" className="profile-panel-title">
            Profile Settings
            <button
              onClick={onClose}
              className="profile-panel-close"
              aria-label="Close profile panel"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </h2>
        </header>

        {/* Content */}
        <main className="profile-panel-content">
          {/* Avatar Section */}
          <section className="profile-panel-avatar-section">
            <div
              className={`profile-panel-avatar-container ${
                isEditMode ? 'edit-mode' : ''
              } ${isDragging ? 'dragging' : ''}`}
              onClick={handleAvatarClick}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              role="button"
              tabIndex={isEditMode ? 0 : -1}
              aria-label={isEditMode ? "Upload avatar photo" : undefined}
              onKeyDown={(e) => {
                if (isEditMode && (e.key === 'Enter' || e.key === ' ')) {
                  e.preventDefault();
                  handleAvatarClick();
                }
              }}
            >
              {avatarPreview ? (
                <img
                  src={avatarPreview}
                  alt="Profile Avatar"
                  className="profile-panel-avatar"
                />
              ) : (
                <div className="profile-panel-avatar-placeholder">
                  <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
              )}

              {isEditMode && (
                <div className="profile-panel-avatar-overlay">
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span className="profile-panel-avatar-text">Upload Photo</span>
                </div>
              )}
            </div>

            {isEditMode && (
              <p className="profile-panel-avatar-hint">Click or drag to upload a new photo</p>
            )}
          </section>

          {/* Form Fields */}
          <form className="profile-panel-form" onSubmit={(e) => e.preventDefault()}>
            {/* Name Field */}
            <div className="profile-panel-field">
              <label htmlFor="profile-name" className="profile-panel-label">
                Name
              </label>
              <input
                id="profile-name"
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                disabled={!isEditMode}
                className="profile-panel-input"
                placeholder="Enter your name"
                maxLength={50}
                aria-required="true"
                aria-invalid={!!error && error.includes('name')}
              />
            </div>

            {/* Email Field (Read-only) */}
            <div className="profile-panel-field">
              <label htmlFor="profile-email" className="profile-panel-label">
                Email
              </label>
              <input
                id="profile-email"
                type="email"
                name="email"
                value={formData.email}
                disabled
                className="profile-panel-input"
                placeholder="Your email address"
                aria-readonly="true"
              />
              <p className="profile-panel-input-hint">Email cannot be changed</p>
            </div>

            {/* Bio Field */}
            <div className="profile-panel-field">
              <label htmlFor="profile-bio" className="profile-panel-label">
                Bio (Optional)
              </label>
              <textarea
                id="profile-bio"
                name="bio"
                value={formData.bio}
                onChange={handleInputChange}
                disabled={!isEditMode}
                rows={4}
                maxLength={200}
                className="profile-panel-input profile-panel-textarea"
                placeholder="Tell us about yourself..."
                aria-describedby="bio-character-count"
              />
              {isEditMode && (
                <p id="bio-character-count" className="profile-panel-character-count">
                  {formData.bio.length}/200 characters
                </p>
              )}
            </div>
          </form>

          {/* Error Message */}
          {error && (
            <div className="profile-panel-error" role="alert">
              <p className="profile-panel-error-text">{error}</p>
            </div>
          )}
        </main>

        {/* Footer Actions */}
        <footer className="profile-panel-footer">
          {isEditMode ? (
            <>
              <button
                onClick={handleEditToggle}
                disabled={isLoading}
                className="profile-panel-button profile-panel-button-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={isLoading}
                className="profile-panel-button profile-panel-button-primary"
                aria-busy={isLoading}
              >
                {isLoading && (
                  <svg className="profile-panel-spinner" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                )}
                Save Changes
              </button>
            </>
          ) : (
            <button
              onClick={handleEditToggle}
              className="profile-panel-button profile-panel-button-primary"
            >
              Edit Profile
            </button>
          )}
        </footer>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
          aria-label="Upload avatar image"
        />
      </div>
    </div>
  );
};

export default ProfilePanel;