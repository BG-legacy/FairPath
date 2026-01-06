import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './IntakePage.css';
import intakeService, { 
  RIASEC_CATEGORIES, 
  IntakeRequest, 
  IntakeResponse,
  ValidationErrors 
} from '../services/intake';

interface Particle {
  x: number;
  y: number;
  size: number;
  opacity: number;
  speed: number;
}

function IntakePage(): JSX.Element {
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  // Form state
  const [skills, setSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState<string>('');
  const [interests, setInterests] = useState<string[]>([]);
  const [interestsText, setInterestsText] = useState<string>('');
  const [useRIASEC, setUseRIASEC] = useState<boolean>(true);
  const [minWage, setMinWage] = useState<number | ''>('');
  const [maxHours, setMaxHours] = useState<number | ''>('');
  const [flexibleHours, setFlexibleHours] = useState<boolean>(false);
  const [remotePreferred, setRemotePreferred] = useState<boolean>(false);
  const [locationPreference, setLocationPreference] = useState<string>('');
  const [maxEducationLevel, setMaxEducationLevel] = useState<number>(5);
  const [impact, setImpact] = useState<number>(3.5);
  const [stability, setStability] = useState<number>(3.5);
  const [flexibility, setFlexibility] = useState<number>(3.5);
  
  // Form state
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [normalizedProfile, setNormalizedProfile] = useState<IntakeResponse | null>(null);
  const [submitError, setSubmitError] = useState<string>('');

  // Handle skill input
  const handleSkillKeyDown = (e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === 'Enter' && skillInput.trim()) {
      e.preventDefault();
      if (!skills.includes(skillInput.trim())) {
        setSkills([...skills, skillInput.trim()]);
        setSkillInput('');
        setErrors({ ...errors, skills: undefined });
      }
    }
  };

  const removeSkill = (skillToRemove: string): void => {
    setSkills(skills.filter(skill => skill !== skillToRemove));
  };

  // Handle RIASEC interests
  const toggleRIASEC = (category: string): void => {
    if (interests.includes(category)) {
      setInterests(interests.filter(interest => interest !== category));
    } else {
      setInterests([...interests, category]);
    }
    setErrors({ ...errors, interests: undefined });
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setSubmitError('');
    setErrors({});
    setIsSubmitting(true);

    try {
      // Build request
      const constraints: any = {};
      
      if (minWage !== '') {
        constraints.cost = { min_wage: Number(minWage) };
      }
      
      if (maxHours !== '' || flexibleHours) {
        const timeConstraints: any = {};
        if (maxHours !== '') {
          timeConstraints.max_hours = Number(maxHours);
        }
        if (flexibleHours) {
          timeConstraints.flexible_hours = flexibleHours;
        }
        if (Object.keys(timeConstraints).length > 0) {
          constraints.time = timeConstraints;
        }
      }
      
      if (remotePreferred || locationPreference.trim()) {
        const locationConstraints: any = {};
        if (remotePreferred) {
          locationConstraints.remote_preferred = remotePreferred;
        }
        if (locationPreference.trim()) {
          locationConstraints.location_preference = locationPreference.trim();
        }
        constraints.location = locationConstraints;
      }
      
      if (maxEducationLevel !== undefined) {
        constraints.max_education_level = maxEducationLevel;
      }

      const request: IntakeRequest = {
        skills: skills.length > 0 ? skills : undefined,
        interests: useRIASEC 
          ? (interests.length > 0 ? interests : undefined)
          : (interestsText.trim() || undefined),
        constraints: Object.keys(constraints).length > 0 ? constraints : undefined,
        values: {
          impact,
          stability,
          flexibility
        }
      };

      // Validate
      const validationErrors = intakeService.validateIntakeRequest(request);
      if (Object.keys(validationErrors).length > 0) {
        setErrors(validationErrors);
        setIsSubmitting(false);
        return;
      }

      // Submit
      const result = await intakeService.normalizeUserProfile(request);
      setNormalizedProfile(result);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : 'Failed to submit form');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Canvas animation (same as Home page)
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

  return (
    <div className="intake-page">
      <canvas ref={canvasRef} className="particles-canvas" />
      <div className="intake-container">
        <button className="back-button" onClick={() => navigate('/')}>
          ← Back to Home
        </button>
        
        <div className="intake-content">
          <h1 className="intake-title">Create Your Profile</h1>
          
          {!normalizedProfile ? (
            <form className="intake-form" onSubmit={handleSubmit}>
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
                  {errors.skills && <span className="error-message">{errors.skills}</span>}
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
                <label className="form-label">Interests</label>
                <div className="interest-toggle-container">
                  <button
                    type="button"
                    className={`toggle-button ${useRIASEC ? 'active' : ''}`}
                    onClick={() => setUseRIASEC(true)}
                  >
                    RIASEC Categories
                  </button>
                  <button
                    type="button"
                    className={`toggle-button ${!useRIASEC ? 'active' : ''}`}
                    onClick={() => setUseRIASEC(false)}
                  >
                    Text Description
                  </button>
                </div>
                
                {useRIASEC ? (
                  <div className="riasec-container">
                    {RIASEC_CATEGORIES.map((category) => (
                      <label key={category} className="riasec-checkbox">
                        <input
                          type="checkbox"
                          checked={interests.includes(category)}
                          onChange={() => toggleRIASEC(category)}
                        />
                        <span>{category}</span>
                      </label>
                    ))}
                    {errors.interests && <span className="error-message">{errors.interests}</span>}
                  </div>
                ) : (
                  <div>
                    <textarea
                      className="form-textarea"
                      placeholder="Describe your interests..."
                      value={interestsText}
                      onChange={(e) => {
                        setInterestsText(e.target.value);
                        setErrors({ ...errors, interests: undefined });
                      }}
                      rows={4}
                    />
                    {errors.interests && <span className="error-message">{errors.interests}</span>}
                  </div>
                )}
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
                    value={minWage}
                    onChange={(e) => {
                      const val = e.target.value;
                      setMinWage(val === '' ? '' : Number(val));
                    }}
                    min="0"
                    step="0.01"
                  />
                </div>

                <div className="constraint-row">
                  <label className="form-label">Max Hours per Week</label>
                  <input
                    type="number"
                    className="form-input"
                    placeholder="e.g., 40"
                    value={maxHours}
                    onChange={(e) => {
                      const val = e.target.value;
                      setMaxHours(val === '' ? '' : Number(val));
                    }}
                    min="1"
                    max="168"
                  />
                </div>

                <div className="constraint-row checkbox-row">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={flexibleHours}
                      onChange={(e) => setFlexibleHours(e.target.checked)}
                    />
                    <span>Flexible Hours</span>
                  </label>
                </div>

                <div className="constraint-row checkbox-row">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={remotePreferred}
                      onChange={(e) => setRemotePreferred(e.target.checked)}
                    />
                    <span>Remote Preferred</span>
                  </label>
                </div>

                <div className="constraint-row">
                  <label className="form-label">Location Preference</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g., New York, NY"
                    value={locationPreference}
                    onChange={(e) => setLocationPreference(e.target.value)}
                  />
                </div>

                <div className="constraint-row">
                  <label className="form-label">Max Education Level (0-5)</label>
                  <select
                    className="form-select"
                    value={maxEducationLevel}
                    onChange={(e) => setMaxEducationLevel(Number(e.target.value))}
                  >
                    <option value={0}>0 - No formal education</option>
                    <option value={1}>1 - High school</option>
                    <option value={2}>2 - Some college</option>
                    <option value={3}>3 - Bachelor's degree</option>
                    <option value={4}>4 - Master's degree</option>
                    <option value={5}>5 - Doctorate or professional</option>
                  </select>
                </div>
                {errors.constraints && <span className="error-message">{errors.constraints}</span>}
              </div>

              {/* Values Section */}
              <div className="form-section">
                <h2 className="section-title">Career Values (0-7 scale)</h2>
                
                <div className="slider-container">
                  <label className="slider-label">
                    <span>Impact: {impact.toFixed(1)}</span>
                    <input
                      type="range"
                      className="form-slider"
                      min="0"
                      max="7"
                      step="0.1"
                      value={impact}
                      onChange={(e) => setImpact(Number(e.target.value))}
                    />
                  </label>
                </div>

                <div className="slider-container">
                  <label className="slider-label">
                    <span>Stability: {stability.toFixed(1)}</span>
                    <input
                      type="range"
                      className="form-slider"
                      min="0"
                      max="7"
                      step="0.1"
                      value={stability}
                      onChange={(e) => setStability(Number(e.target.value))}
                    />
                  </label>
                </div>

                <div className="slider-container">
                  <label className="slider-label">
                    <span>Flexibility: {flexibility.toFixed(1)}</span>
                    <input
                      type="range"
                      className="form-slider"
                      min="0"
                      max="7"
                      step="0.1"
                      value={flexibility}
                      onChange={(e) => setFlexibility(Number(e.target.value))}
                    />
                  </label>
                </div>
                {errors.values && <span className="error-message">{errors.values}</span>}
              </div>

              {submitError && <div className="error-banner">{submitError}</div>}

              <button 
                type="submit" 
                className="submit-button"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Processing...' : 'Submit Profile'}
              </button>
            </form>
          ) : (
            <div className="results-container">
              <h2 className="section-title">Normalized Profile Results</h2>
              <div className="results-content">
                <pre className="results-json">
                  {JSON.stringify(normalizedProfile, null, 2)}
                </pre>
              </div>
              <button 
                className="submit-button"
                onClick={() => {
                  setNormalizedProfile(null);
                  setSubmitError('');
                }}
              >
                Create New Profile
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default IntakePage;
