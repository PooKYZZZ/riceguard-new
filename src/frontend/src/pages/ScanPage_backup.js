// src/pages/ScanPage.js
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./ScanPage.css";
import { uploadScan, getRecommendation } from "../api";
import ProfilePanel from "../components/ProfilePanel";
import { tokenStorage } from "../secureStorage";

function ScanPage() {
  const navigate = useNavigate();
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [logoutOpen, setLogoutOpen] = useState(false);
  const [token, setToken] = useState(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [user, setUser] = useState(null);

  // Auth check
  useEffect(() => {
    const t = tokenStorage.getValidatedToken();
    setToken(t);
    if (!t) navigate("/");

    // Load user data from tokenStorage
    const userData = tokenStorage.getUser();
    setUser(userData);
  }, [navigate]);

  // Local fallback (only if backend doesn’t return one)
  const recommendations = {
    "Bacterial Leaf Blight":
      "Remove infected plants immediately and avoid excessive nitrogen fertilizer. Apply copper-based bactericides and ensure proper field drainage to prevent spread.",
    "Brown Spot":
      "Apply balanced fertilizer with potassium and nitrogen. Use fungicides like Mancozeb or Tricyclazole if infection persists. Ensure proper spacing and water management to reduce humidity.",
    "Leaf Smut":
      "Use resistant rice varieties and practice crop rotation. Avoid high nitrogen levels and maintain proper field sanitation. Apply appropriate fungicides if the infection is severe.",
    Healthy:
      "Your rice crop appears healthy. Continue good farming practices, balanced fertilization, proper irrigation, and pest monitoring.",
  };

  // Image select + preview
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        alert('Please upload an image file (JPG, PNG, etc.)');
        e.target.value = ''; // Reset input
        return;
      }
      
      // Validate file size (8MB max)
      const maxSize = 8 * 1024 * 1024; // 8MB in bytes
      if (file.size > maxSize) {
        alert('File size must be less than 8MB. Please choose a smaller image.');
        e.target.value = ''; // Reset input
        return;
      }
      
      setImage(file);
      
      // MEMORY LEAK FIX: Revoke old blob URL before creating new one
      if (preview) {
        URL.revokeObjectURL(preview);
      }
      
      const url = URL.createObjectURL(file);
      setPreview(url);
      setResult(null);
    }
  };

  // Cleanup preview URL on unmount
  useEffect(() => {
    return () => {
      if (preview) {
        URL.revokeObjectURL(preview);
      }
    };
  }, [preview]);

  // Upload + inference
  const handleUpload = async () => {
    if (!image) {
      alert("Please select an image first!");
      return;
    }
    if (!token) {
      alert("You must be logged in to scan.");
      return;
    }

    try {
      setLoading(true);
      setResult(null);

      // Expecting backend to return: { label, confidence, createdAt, ... }
      const data = await uploadScan({ file: image });

      const diseaseKeyRaw = data.label; // e.g. "brown_spot" or "Brown Spot"
      let recText = "";
      try {
        // normalize for API: snake_case if needed
        let key = diseaseKeyRaw;
        if (!/^[a-z_]+$/.test(key)) key = diseaseKeyRaw.toLowerCase().replace(/\s+/g, "_");

        const rec = await getRecommendation(key);
        recText = Array.isArray(rec?.steps) ? rec.steps.join(" ") : "";
      } catch {
        // optional local fallback (may not match keys exactly)
        recText =
          recommendations[diseaseKeyRaw] ||
          recommendations[diseaseKeyRaw?.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase())] ||
          "";
      }

      // Use the actual calibrated confidence from backend
      let rawConfidence = typeof data.confidence === "number"
        ? (data.confidence * 100).toFixed(1)
        : data.confidence;

      let displayConfidence = rawConfidence;  // No artificial caps
      let needsCalibrationNotice = parseFloat(rawConfidence) > 90;

      const newResult = {
        disease: diseaseKeyRaw,
        confidence: displayConfidence,
        rawConfidence: rawConfidence,
        needsCalibrationNotice,
        recommendation: recText || "No recommendation available.",
        timestamp: data.createdAt,
        top3: data.top3 || null, // Top-3 predictions if available
        alternatives: data.alternatives || [], // Similar diseases that might be confused
      };

      setResult(newResult);
      console.log("Prediction saved:", newResult);
    } catch (error) {
      console.error("Upload error:", error);
      alert("Failed to connect to backend. Please check if FastAPI is running.");
    } finally {
      setLoading(false);
    }

    return; // keep function single-path
  };

  const handleHistory = () => navigate("/history");
  const openLogout = () => setLogoutOpen(true);
  const closeLogout = () => setLogoutOpen(false);
  const confirmLogout = () => {
    setLogoutOpen(false);
    tokenStorage.clearToken();
    navigate("/");
  };

  // Profile panel functions
  const openProfile = () => setProfileOpen(true);
  const closeProfile = () => setProfileOpen(false);

  return (
    <div className="scan-page">
      {/* Header */}
      <div className="scan-header">
        <div className="logo-section">
          <img
            src={`${process.env.PUBLIC_URL}/logo.png`}
            alt="Rice Guard Logo"
            className="scan-logo"
          />
        </div>
        <nav className="nav-links">
          <button onClick={openLogout}>Log Out</button>
          <button className="active">Scan</button>
          <button onClick={handleHistory}>History</button>
          <button onClick={openProfile} className="profile-btn">
            {user?.name || user?.email || 'Profile'}
          </button>
        </nav>
      </div>

      {/* Content */}
      <div className="scan-content">
        <div className="upload-card">
          {/* Image Upload Box */}
          <label htmlFor="file-upload" className="upload-box">
            {preview ? (
              <img
                src={preview}
                alt="Uploaded preview"
                className="uploaded-preview"
              />
            ) : (
              <>
                <div className="upload-icon">📷</div>
                <p>Upload Image</p>
              </>
            )}
          </label>

          <input
            id="file-upload"
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            hidden
          />

          {/* Upload Button */}
          <button
            className="upload-btn"
            onClick={handleUpload}
            disabled={loading || !image}
          >
            {loading ? "Analyzing..." : "SCAN IMAGE"}
          </button>

          {/* Result */}
          {result && (
            <div className="result-box">
              <h3>Result</h3>
              <p>
                <strong>Disease:</strong> {result.disease}
              </p>
              <p>
                <strong>Confidence:</strong>{" "}
                <span className={`confidence-badge ${result.disease === 'uncertain' ? 'uncertain' : result.confidence > 70 ? 'high' : result.confidence > 50 ? 'medium' : 'low'}`}>
                  {result.confidence}%
                </span>
                {result.needsCalibrationNotice && (
                  <span className="calibration-notice" title={`Very high confidence detected: ${result.rawConfidence}%`}>
                    <small> (very high confidence)</small>
                  </span>
                )}
              </p>

              {/* Disease Similarity Warning */}
              {result.alternatives && result.alternatives.length > 0 && (
                <div className="similar-diseases-warning">
                  <p>⚠️ This disease can be confused with: {result.alternatives.map(alt =>
                    alt.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                  ).join(', ')}. Consider consulting an expert for confirmation.</p>
                </div>
              )}

              {/* Top-3 Predictions */}
              {result.top3 && result.top3.length > 0 && (
                <div className="top3-predictions">
                  <h4>Top Predictions:</h4>
                  {result.top3.map((pred, index) => (
                    <div key={index} className={`prediction-rank prediction-${index + 1}`}>
                      <span className="rank">#{index + 1}</span>
                      <span className="label">{pred.label.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                      <span className="confidence">{(pred.confidence * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )}

              {result.disease === 'uncertain' && (
                <div className="uncertainty-notice">
                  <p>⚠️ Low confidence detected. Try using a clearer, better-lit image focused on the affected area.</p>
                  <div className="improvement-tips">
                    <strong>Tips for better results:</strong>
                    <ul>
                      <li>Use bright, even lighting</li>
                      <li>Focus on the affected area</li>
                      <li>Include single leaf per image</li>
                      <li>Avoid shadows and glare</li>
                    </ul>
                  </div>
                </div>
              )}

              <p>
                <strong>Recommendation:</strong> {result.recommendation}
              </p>
              <p>
                <strong>Analyzed On:</strong>{" "}
                {result.timestamp
                  ? new Date(result.timestamp).toLocaleString()
                  : "-"}
              </p>
            </div>
          )}
        </div>

        {/* Instruction Box */}
        <div className="instruction-box">
          <p>To begin analysis, upload your rice leaf image and ensure</p>
          <p>the photo is clear and well-lit for accurate detection.</p>
        </div>
      </div>

      {/* Logout Modal */}
      {logoutOpen && (
        <div className="modal-backdrop" onClick={closeLogout}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Log out</h2>
            <p>Are you sure you want to log out?</p>
            <div className="modal-actions">
              <button className="btn-outline" type="button" onClick={closeLogout}>
                Cancel
              </button>
              <button className="btn-primary" type="button" onClick={confirmLogout}>
                Log out
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Profile Panel */}
      <ProfilePanel
        isOpen={profileOpen}
        onClose={closeProfile}
        user={user}
      />
    </div>
  );
}

export default ScanPage;
