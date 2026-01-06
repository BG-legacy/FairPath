import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './GuardedRecommendationsPage.css';
import recommendationsGuardedService, {
  GuardedRecommendationRequest,
  GuardedRecommendationsResponse,
  GuardedRecommendation,
  GuardrailsInfo,
} from '../services/recommendationsGuarded';
import { RIASEC_CATEGORIES } from '../services/intake';

interface Particle {
  x: number;
  y: number;
  size: number;
  opacity: number;
  speed: number;
}

function GuardedRecommendationsPage(): JSX.Element {
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
  const [useML, setUseML] = useState<boolean>(true);
  const [topN, setTopN] = useState<number>(5);

  // Results state
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [results, setResults] = useState<GuardedRecommendationsResponse | null>(null);
  const [guardrailsInfo, setGuardrailsInfo] = useState<GuardrailsInfo | null>(null);
  const [demographicRejection, setDemographicRejection] = useState<string>('');

  // Load guardrails info on mount
  useEffect(() => {
    const loadGuardrailsInfo = async (): Promise<void> => {
      try {
        const info = await recommendationsGuardedService.getGuardrailsInfo();
        setGuardrailsInfo(info);
      } catch (err) {
        console.error('Failed to load guardrails info:', err);
      }
    };
    loadGuardrailsInfo();
  }, []);

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
    setError('');
    setDemographicRejection('');
    setIsLoading(true);
    setResults(null);

    try {
      const request: GuardedRecommendationRequest = {
        skills: skills.length > 0 ? skills : undefined,
        interests: Object.keys(interests).length > 0 ? interests : undefined,
        work_values: workValues,
        constraints: Object.keys(constraints).length > 0 ? constraints : undefined,
        top_n: topN,
        use_ml: useML,
      };

      const response = await recommendationsGuardedService.getGuardedRecommendations(request);
      
      // Check if we got minimum recommendations
      if (response.recommendations.length < 3) {
        setError(`Warning: Only ${response.recommendations.length} recommendations returned. Minimum of 3 expected.`);
      }
      
      setResults(response);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get guarded recommendations';
      
      // Check if error is related to demographic data rejection
      if (errorMessage.toLowerCase().includes('demographic') || 
          errorMessage.toLowerCase().includes('blocked') ||
          errorMessage.toLowerCase().includes('guardrail')) {
        setDemographicRejection(errorMessage);
      } else {
        setError(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
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
        return '#fbbf24';
      case 'Low':
        return '#f87171';
      default:
        return '#ffffff';
    }
  };

  return (
    <div className="guarded-recommendations-page">
      <canvas ref={canvasRef} className="particles-canvas" />
      <div className="guarded-recommendations-container">
        <button className="back-button" onClick={() => navigate('/')}>
          ← Back to Home
        </button>

        <div className="guarded-recommendations-content">
          <h1 className="guarded-recommendations-title">Guarded Career Recommendations</h1>

          {/* Guardrails Info Display */}
          {guardrailsInfo && (
            <div className="guardrails-info">
              <h2 className="section-title">Guardrails Information</h2>
              <div className="guardrails-content">
                <div className="guardrails-item">
                  <span className="guardrails-label">Active Guardrails:</span>
                  <ul className="guardrails-list">
                    {guardrailsInfo.guardrails.map((guardrail, idx) => (
                      <li key={idx}>{guardrail}</li>
                    ))}
                  </ul>
                </div>
                <div className="guardrails-item">
                  <span className="guardrails-label">Blocked Keywords:</span>
                  <div className="blocked-keywords">
                    {guardrailsInfo.demographic_keywords_blocked.length > 0 ? (
                      guardrailsInfo.demographic_keywords_blocked.map((keyword, idx) => (
                        <span key={idx} className="keyword-tag">{keyword}</span>
                      ))
                    ) : (
                      <span className="no-keywords">None</span>
                    )}
                  </div>
                </div>
                <div className="guardrails-item">
                  <span className="guardrails-label">Minimum Recommendations:</span>
                  <span className="guardrails-value">{guardrailsInfo.minimum_recommendations}</span>
                </div>
                <div className="guardrails-item">
                  <span className="guardrails-label">Default Recommendations:</span>
                  <span className="guardrails-value">{guardrailsInfo.default_recommendations}</span>
                </div>
              </div>
            </div>
          )}

          {/* Demographic Rejection Message */}
          {demographicRejection && (
            <div className="demographic-rejection">
              <h3 className="rejection-title">⚠️ Demographic Data Detected</h3>
              <p className="rejection-message">{demographicRejection}</p>
              <p className="rejection-note">
                Please remove any demographic information from your input and try again.
              </p>
            </div>
          )}

          {!results ? (
            <form className="guarded-recommendations-form" onSubmit={handleSubmit}>
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

              {/* ML Toggle */}
              <div className="form-section">
                <div className="toggle-container">
                  <label className="toggle-label">
                    <span>Use ML Model</span>
                    <button
                      type="button"
                      className={`toggle-switch ${useML ? 'active' : ''}`}
                      onClick={() => setUseML(!useML)}
                    >
                      <span className="toggle-slider"></span>
                    </button>
                  </label>
                </div>
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

              {error && <div className="error-banner">{error}</div>}

              <button
                type="submit"
                className="submit-button"
                disabled={isLoading}
              >
                {isLoading ? 'Loading...' : 'Get Guarded Recommendations'}
              </button>
            </form>
          ) : (
            <div className="results-container">
              <div className="results-header">
                <h2 className="section-title">
                  Recommendations ({results.method}) - {results.recommendations.length} results
                </h2>
                <button
                  className="back-button"
                  onClick={() => {
                    setResults(null);
                    setError('');
                    setDemographicRejection('');
                  }}
                >
                  New Search
                </button>
              </div>

              {/* Minimum Recommendations Warning */}
              {results.recommendations.length < 3 && (
                <div className="warning-banner">
                  ⚠️ Warning: Only {results.recommendations.length} recommendation(s) returned. 
                  Guardrails require a minimum of 3 recommendations.
                </div>
              )}

              {/* Recommendations Grid */}
              <div className="careers-section">
                <div className="careers-grid">
                  {results.recommendations.map((career: GuardedRecommendation) => (
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
                          <span className="score-value">{career.score.toFixed(2)}</span>
                        </div>
                        {career.soc_code && (
                          <div className="career-meta">
                            <span>SOC: {career.soc_code}</span>
                          </div>
                        )}
                      </div>

                      {/* Explanation */}
                      {career.explanation && (
                        <div className="explanation-section">
                          <h5 className="explanation-title">Explanation</h5>
                          {career.explanation.why_points && career.explanation.why_points.length > 0 && (
                            <ul className="why-points-list">
                              {career.explanation.why_points.map((point, idx) => (
                                <li key={idx}>{point}</li>
                              ))}
                            </ul>
                          )}
                          {career.explanation.top_contributing_skills && career.explanation.top_contributing_skills.length > 0 && (
                            <div className="top-skills">
                              <h6 className="top-skills-title">Top Contributing Skills:</h6>
                              <ul className="skills-list">
                                {career.explanation.top_contributing_skills.slice(0, 5).map((skill, idx) => (
                                  <li key={idx}>
                                    {skill.feature} ({skill.contribution > 0 ? '+' : ''}{skill.contribution.toFixed(2)})
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default GuardedRecommendationsPage;

