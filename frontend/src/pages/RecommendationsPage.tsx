import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './RecommendationsPage.css';
import {
  RecommendationRequest,
  CareerRecommendation,
  WhyNarrative,
} from '../services/recommendations';
import { RIASEC_CATEGORIES } from '../services/intake';
import { useGetEnhancedRecommendations } from '../hooks';
import { CareerCardSkeleton } from '../components/LoadingSkeleton';
import { LinearProgress } from '../components/ProgressIndicator';
import { ValidationErrorDisplay } from '../components/ValidationErrorDisplay';
import { ApiError } from '../services/apiClient';

interface Particle {
  x: number;
  y: number;
  size: number;
  opacity: number;
  speed: number;
}

function RecommendationsPage(): JSX.Element {
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Form state
  const [skills, setSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState<string>('');
  const [interests, setInterests] = useState<Record<string, number>>({});
  const [workValues, setWorkValues] = useState<Record<string, number>>({
    impact: 3.5,
    stability: 3.5,
    flexibility: 3.5,
  });
  const [constraints, setConstraints] = useState<{
    min_wage?: number;
    remote_preferred?: boolean;
    max_education_level?: number;
  }>({});
  const [topN, setTopN] = useState<number>(5);

  // Results state - using React Query mutation hook
  const getRecommendations = useGetEnhancedRecommendations({
    onSuccess: (data) => {
      // Show success toast
      const count = data.careers?.length || 0;
      if (count > 0) {
        // Success toast is shown automatically by QueryProvider
        // But we can add a custom message here if needed
      }
      // Optionally save selected career to global store
      if (data.careers && data.careers.length > 0) {
        // You can set the first recommendation as selected if desired
        // useAppStore.getState().setSelectedCareer(data.careers[0]);
      }
    },
    onError: (error) => {
      // Error toast is shown automatically by QueryProvider
      console.error('Failed to get recommendations:', error);
    },
  });

  const results = getRecommendations.data || null;
  const isLoading = getRecommendations.isPending;
  const error = getRecommendations.error as ApiError | null;
  
  // Extract validation errors if present
  const validationErrors = Array.isArray(error?.data?.details) ? error.data.details : [];
  const errorMessage = error?.message || '';

  // Handle skill input
  const handleSkillKeyDown = (e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === 'Enter' && skillInput.trim()) {
      e.preventDefault();
      if (!skills.includes(skillInput.trim())) {
        setSkills([...skills, skillInput.trim()]);
        setSkillInput('');
      }
    }
  };

  const removeSkill = (skillToRemove: string): void => {
    setSkills(skills.filter(skill => skill !== skillToRemove));
  };

  // Handle RIASEC interests
  const handleInterestChange = (category: string, value: number): void => {
    setInterests({ ...interests, [category]: value });
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();

    const request: RecommendationRequest = {
      skills: skills.length > 0 ? skills : undefined,
      interests: Object.keys(interests).length > 0 ? interests : undefined,
      work_values: workValues,
      constraints: Object.keys(constraints).length > 0 ? constraints : undefined,
      top_n: topN,
      use_ml: true, // Always use ML, with OpenAI fallback for poor matches
    };

    // Use mutation hook - handles loading, error, and success states automatically
    getRecommendations.mutate(request);
  };

  // Canvas animation
  useEffect(() => {
    const canvas: HTMLCanvasElement | null = canvasRef.current;
    if (!canvas) return;

    const ctx: CanvasRenderingContext2D | null = canvas.getContext('2d');
    if (!ctx) return;

    const resizeCanvas = (): void => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const particles: Particle[] = [];
    const isMobile: boolean = window.innerWidth < 768;
    const particleCount: number = isMobile
      ? Math.min(Math.floor(window.innerWidth * 0.1), 50)
      : Math.min(window.innerWidth * 0.15, 100);

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 2 + 0.5,
        opacity: Math.random(),
        speed: Math.random() * 0.5 + 0.1,
      });
    }

    const animate = (): void => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach((particle: Particle) => {
        particle.opacity += Math.sin(Date.now() * 0.001 + particle.x) * 0.01;
        particle.opacity = Math.max(0.2, Math.min(1, particle.opacity));

        ctx.beginPath();
        ctx.fillStyle = `rgba(255, 255, 255, ${particle.opacity})`;
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fill();
      });

      requestAnimationFrame(animate);
    };

    animate();

    return (): void => {
      window.removeEventListener('resize', resizeCanvas);
    };
  }, []);

  const getConfidenceColor = (confidence: string): string => {
    switch (confidence) {
      case 'High':
        return '#4ade80';
      case 'Med':
      case 'Medium':  // Support both for backwards compatibility
        return '#fbbf24';
      case 'Low':
        return '#f87171';
      case 'Very Low':
        return '#ef4444';  // Darker red for very low confidence
      default:
        return '#ffffff';
    }
  };

  return (
    <div className="recommendations-page">
      <canvas ref={canvasRef} className="particles-canvas" />
      <div className="recommendations-container">
        <button className="back-button" onClick={() => navigate('/')}>
          ← Back to Home
        </button>

        <div className="recommendations-content">
          <h1 className="recommendations-title">Career Recommendations</h1>

          {!results && !isLoading ? (
            <form className="recommendations-form" onSubmit={handleSubmit}>
              {/* Skills Section */}
              <div className="form-section">
                <label className="form-label">Skills</label>
                <div className="skill-input-container">
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Type a skill and press Enter"
                    value={skillInput}
                    onChange={(e) => setSkillInput(e.target.value)}
                    onKeyDown={handleSkillKeyDown}
                  />
                </div>
                {skills.length > 0 && (
                  <div className="skills-list">
                    {skills.map((skill, index) => (
                      <span key={index} className="skill-tag">
                        {skill}
                        <button
                          type="button"
                          className="skill-remove"
                          onClick={() => removeSkill(skill)}
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Interests Section */}
              <div className="form-section">
                <label className="form-label">Interests (RIASEC Categories)</label>
                <div className="riasec-container">
                  {RIASEC_CATEGORIES.map((category) => (
                    <div key={category} className="riasec-slider">
                      <label className="slider-label">
                        <span>{category}</span>
                        <div className="slider-wrapper">
                          <input
                            type="range"
                            className="form-slider"
                            min="0"
                            max="7"
                            step="0.1"
                            value={interests[category] || 0}
                            onChange={(e) => handleInterestChange(category, Number(e.target.value))}
                          />
                          <span className="slider-value">{interests[category]?.toFixed(1) || '0.0'}</span>
                        </div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Work Values Section */}
              <div className="form-section">
                <h2 className="section-title">Work Values (0-7 scale)</h2>
                <div className="slider-container">
                  <label className="slider-label">
                    <span>Impact: {workValues.impact?.toFixed(1) || '0.0'}</span>
                    <input
                      type="range"
                      className="form-slider"
                      min="0"
                      max="7"
                      step="0.1"
                      value={workValues.impact || 0}
                      onChange={(e) => setWorkValues({ ...workValues, impact: Number(e.target.value) })}
                    />
                  </label>
                </div>
                <div className="slider-container">
                  <label className="slider-label">
                    <span>Stability: {workValues.stability?.toFixed(1) || '0.0'}</span>
                    <input
                      type="range"
                      className="form-slider"
                      min="0"
                      max="7"
                      step="0.1"
                      value={workValues.stability || 0}
                      onChange={(e) => setWorkValues({ ...workValues, stability: Number(e.target.value) })}
                    />
                  </label>
                </div>
                <div className="slider-container">
                  <label className="slider-label">
                    <span>Flexibility: {workValues.flexibility?.toFixed(1) || '0.0'}</span>
                    <input
                      type="range"
                      className="form-slider"
                      min="0"
                      max="7"
                      step="0.1"
                      value={workValues.flexibility || 0}
                      onChange={(e) => setWorkValues({ ...workValues, flexibility: Number(e.target.value) })}
                    />
                  </label>
                </div>
              </div>

              {/* Constraints Section */}
              <div className="form-section">
                <h2 className="section-title">Constraints</h2>
                <div className="constraint-row">
                  <label className="form-label">Minimum Wage ($)</label>
                  <input
                    type="number"
                    className="form-input"
                    placeholder="e.g., 15.00"
                    value={constraints.min_wage || ''}
                    onChange={(e) => {
                      const val = e.target.value;
                      setConstraints({ ...constraints, min_wage: val ? Number(val) : undefined });
                    }}
                    min="0"
                    step="0.01"
                  />
                </div>
                <div className="constraint-row checkbox-row">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={constraints.remote_preferred || false}
                      onChange={(e) => setConstraints({ ...constraints, remote_preferred: e.target.checked || undefined })}
                    />
                    <span>Remote Preferred</span>
                  </label>
                </div>
                <div className="constraint-row">
                  <label className="form-label">Max Education Level (0-5)</label>
                  <select
                    className="form-select"
                    value={constraints.max_education_level ?? ''}
                    onChange={(e) => {
                      const val = e.target.value;
                      setConstraints({ ...constraints, max_education_level: val ? Number(val) : undefined });
                    }}
                  >
                    <option value="">No limit</option>
                    <option value={0}>0 - No formal education</option>
                    <option value={1}>1 - High school</option>
                    <option value={2}>2 - Some college</option>
                    <option value={3}>3 - Bachelor's degree</option>
                    <option value={4}>4 - Master's degree</option>
                    <option value={5}>5 - Doctorate or professional</option>
                  </select>
                </div>
              </div>

              {/* Number of Recommendations */}
              <div className="form-section">
                <div className="constraint-row">
                  <label className="form-label">Number of Recommendations (1-20)</label>
                  <input
                    type="number"
                    className="form-input"
                    min="1"
                    max="20"
                    value={topN}
                    onChange={(e) => setTopN(Math.max(1, Math.min(20, Number(e.target.value) || 5)))}
                  />
                </div>
              </div>

              {/* Validation Errors */}
              {validationErrors.length > 0 && (
                <ValidationErrorDisplay errors={validationErrors} />
              )}

              {/* General Error Message */}
              {errorMessage && validationErrors.length === 0 && (
                <div className="error-banner">{errorMessage}</div>
              )}

              {/* Loading Progress */}
              {isLoading && (
                <div style={{ marginBottom: '1rem' }}>
                  <LinearProgress 
                    message="Getting your career recommendations..." 
                    indeterminate={true}
                  />
                </div>
              )}

              <button
                type="submit"
                className="submit-button"
                disabled={isLoading}
              >
                {isLoading ? 'Loading...' : 'Get Recommendations'}
              </button>
            </form>
          ) : isLoading ? (
            <div className="loading-container">
              <LinearProgress 
                message="Analyzing your profile and generating recommendations..." 
                indeterminate={true}
              />
              <div className="skeleton-grid" style={{ marginTop: '2rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
                <CareerCardSkeleton />
                <CareerCardSkeleton />
                <CareerCardSkeleton />
              </div>
            </div>
          ) : results ? (
            <div className="results-container">
              <div className="results-header">
                <h2 className="section-title">Recommendations</h2>
                <button
                  className="back-button"
                  onClick={() => {
                    // Reset mutation state
                    getRecommendations.reset();
                  }}
                >
                  New Search
                </button>
              </div>

              {/* Main Recommendations */}
              <div className="careers-section">
                <h3 className="subsection-title">Top Recommendations</h3>
                <div className="careers-grid">
                  {results.careers && results.careers.length > 0 ? results.careers.map((career: CareerRecommendation) => (
                    <div key={career.career_id} className="career-card">
                      <div className="career-header">
                        <h4 className="career-name">{career.name}</h4>
                        <span
                          className="confidence-badge"
                          style={{ backgroundColor: getConfidenceColor(career.confidence) }}
                        >
                          {career.confidence}
                        </span>
                      </div>
                      <div className="career-details">
                        <div className="career-score">
                          <span className="score-label">Score:</span>
                          <span className="score-value">{(career.score ?? 0).toFixed(2)}</span>
                          {career.confidence_band?.score_range && (
                            <span className="score-range">
                              ({(career.confidence_band.score_range[0] ?? 0).toFixed(2)} - {(career.confidence_band.score_range[1] ?? 0).toFixed(2)})
                            </span>
                          )}
                        </div>
                        {career.soc_code && (
                          <div className="career-meta">
                            <span>SOC: {career.soc_code}</span>
                          </div>
                        )}
                      </div>

                      {/* Why Narrative */}
                      {career.why && (
                        <div className="why-section">
                          <h5 className="why-title">Why this career?</h5>
                          <p className="why-text">
                            {typeof career.why === 'string' 
                              ? career.why 
                              : (career.why as WhyNarrative)?.summary || (career.why as WhyNarrative)?.primary || 'This career matches your profile based on skill and interest alignment.'}
                          </p>
                          {typeof career.why === 'object' && (career.why as WhyNarrative)?.points && Array.isArray((career.why as WhyNarrative).points) && (career.why as WhyNarrative).points!.length > 0 && (
                            <ul className="why-points">
                              {(career.why as WhyNarrative).points!.slice(0, 3).map((point: string, idx: number) => (
                                <li key={idx}>{point}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      )}

                      {/* Explainability */}
                      {career.explainability && career.explainability.top_features && (
                        <div className="explainability-section">
                          <h5 className="explainability-title">Top Contributing Features</h5>
                          <ul className="features-list">
                            {career.explainability.top_features.slice(0, 5).map((feature, idx) => (
                              <li key={idx} className="feature-item">
                                <span className="feature-name">{feature.feature}</span>
                                <span className="feature-contribution">
                                  {((feature.contribution ?? 0) > 0 ? '+' : '')}{(feature.contribution ?? 0).toFixed(2)}
                                </span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Confidence Band */}
                      {career.confidence_band && (
                        <div className="confidence-band">
                          <span className="band-label">Confidence Level:</span>
                          <span className="band-value">{career.confidence_band.level}</span>
                        </div>
                      )}
                    </div>
                  )) : <div className="no-results">No recommendations available</div>}
                </div>
              </div>

              {/* Alternatives Section - Only show high-quality alternatives */}
              {results.alternatives && results.alternatives.length > 0 && (
                <div className="alternatives-section">
                  <h3 className="subsection-title">Additional Career Options</h3>
                  <div className="careers-grid">
                    {results.alternatives.map((career: CareerRecommendation) => (
                      <div key={career.career_id} className="career-card alternative">
                        <div className="career-header">
                          <h4 className="career-name">{career.name}</h4>
                          <span
                            className="confidence-badge"
                            style={{ backgroundColor: getConfidenceColor(career.confidence) }}
                          >
                            {career.confidence}
                          </span>
                        </div>
                        <div className="career-details">
                          <div className="career-score">
                            <span className="score-label">Score:</span>
                            <span className="score-value">{(career.score ?? 0).toFixed(2)}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default RecommendationsPage;

