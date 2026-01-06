import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './CoachPage.css';
import coachService, {
  CoachNextStepsRequest,
  CoachingNextSteps,
  RIASECCategory,
  WorkValue,
} from '../services/coach';
import { RIASEC_CATEGORIES } from '../services/intake';
import dataService, { OccupationCatalog } from '../services/data';

interface Particle {
  x: number;
  y: number;
  size: number;
  opacity: number;
  speed: number;
}

function CoachPage(): JSX.Element {
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Form state
  const [careerName, setCareerName] = useState<string>('');
  const [careerId, setCareerId] = useState<string>('');
  const [careerSearch, setCareerSearch] = useState<string>('');
  const [careerResults, setCareerResults] = useState<OccupationCatalog[]>([]);
  const [showResults, setShowResults] = useState<boolean>(false);
  const [skills, setSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState<string>('');
  const [interests, setInterests] = useState<Record<string, number>>({});
  const [workValues, setWorkValues] = useState<Record<string, number>>({});
  const [includePortfolio, setIncludePortfolio] = useState<boolean>(false);
  const [includeInterview, setIncludeInterview] = useState<boolean>(false);

  // Results state
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [results, setResults] = useState<CoachingNextSteps | null>(null);

  // Search for careers
  const searchCareers = async (query: string): Promise<void> => {
    if (!query.trim()) {
      setCareerResults([]);
      setShowResults(false);
      return;
    }

    try {
      const response = await dataService.getOccupationCatalog({ search: query, limit: 10 });
      // Sort results alphabetically by occupation name
      const sortedResults = [...response.occupations].sort((a, b) =>
        a.occupation.name.localeCompare(b.occupation.name)
      );
      setCareerResults(sortedResults);
      setShowResults(true);
    } catch (err) {
      console.error('Failed to search careers:', err);
    }
  };

  // Handle search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      searchCareers(careerSearch);
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [careerSearch]);

  // Select career
  const selectCareer = (career: OccupationCatalog): void => {
    setCareerId(career.occupation.career_id);
    setCareerSearch(career.occupation.name);
    setCareerName(career.occupation.name);
    setShowResults(false);
  };

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

  // Handle work values
  const handleWorkValueChange = (value: string, val: number): void => {
    setWorkValues({ ...workValues, [value]: val });
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    setResults(null);

    if (!careerName.trim()) {
      setError('Career name is required');
      setIsLoading(false);
      return;
    }

    try {
      const request: CoachNextStepsRequest = {
        career_name: careerName,
        career_id: careerId || undefined,
        user_skills: skills.length > 0 ? skills : undefined,
        user_interests: Object.keys(interests).length > 0 ? interests as Record<RIASECCategory, number> : undefined,
        user_work_values: Object.keys(workValues).length > 0 ? workValues as Record<WorkValue, number> : undefined,
        include_portfolio: includePortfolio,
        include_interview: includeInterview,
      };

      const response = await coachService.getNextSteps(request);
      setResults(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get coaching next steps');
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

  const workValueLabels: Record<string, string> = {
    Achievement: 'Achievement',
    'Working Conditions': 'Working Conditions',
    Recognition: 'Recognition',
    Relationships: 'Relationships',
    Support: 'Support',
    Independence: 'Independence',
  };

  return (
    <div className="coach-page">
      <canvas ref={canvasRef} className="particles-canvas" />
      <div className="coach-container">
        <button className="back-button" onClick={() => navigate('/')}>
          ← Back to Home
        </button>

        <div className="coach-content">
          <h1 className="coach-title">Career Coach</h1>

          {!results ? (
            <form className="coach-form" onSubmit={handleSubmit}>
              {/* Career Name (Required) */}
              <div className="form-section">
                <label className="form-label">
                  Career Name <span className="required">*</span>
                </label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Enter career name (e.g., Software Developer)"
                  value={careerName}
                  onChange={(e) => setCareerName(e.target.value)}
                  required
                />
              </div>

              {/* Career ID (Optional) */}
              <div className="form-section">
                <label className="form-label">Career ID (Optional)</label>
                <div className="career-search-container">
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Search for a career to auto-fill ID..."
                    value={careerSearch}
                    onChange={(e) => {
                      setCareerSearch(e.target.value);
                      if (!e.target.value) {
                        setCareerId('');
                      }
                    }}
                    onFocus={() => {
                      if (careerResults.length > 0) {
                        setShowResults(true);
                      }
                    }}
                  />
                  {showResults && careerResults.length > 0 && (
                    <div className="career-results">
                      {careerResults.map((career) => (
                        <button
                          key={career.occupation.career_id}
                          type="button"
                          className="career-result-item"
                          onClick={() => selectCareer(career)}
                        >
                          <div className="career-result-name">{career.occupation.name}</div>
                          {career.occupation.soc_code && (
                            <div className="career-result-code">SOC: {career.occupation.soc_code}</div>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                {careerId && (
                  <div className="selected-career">
                    <span>Selected: {careerSearch} (ID: {careerId})</span>
                  </div>
                )}
              </div>

              {/* Skills (Optional) */}
              <div className="form-section">
                <label className="form-label">User Skills (Optional)</label>
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

              {/* Interests (Optional) */}
              <div className="form-section">
                <label className="form-label">User Interests - RIASEC Categories (Optional)</label>
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

              {/* Work Values (Optional) */}
              <div className="form-section">
                <label className="form-label">User Work Values (Optional, 0-7 scale)</label>
                <div className="values-container">
                  {Object.keys(workValueLabels).map((value) => (
                    <div key={value} className="value-slider">
                      <label className="slider-label">
                        <span>{workValueLabels[value]}: {workValues[value]?.toFixed(1) || '0.0'}</span>
                        <input
                          type="range"
                          className="form-slider"
                          min="0"
                          max="7"
                          step="0.1"
                          value={workValues[value] || 0}
                          onChange={(e) => handleWorkValueChange(value, Number(e.target.value))}
                        />
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Checkboxes */}
              <div className="form-section">
                <div className="checkbox-container">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={includePortfolio}
                      onChange={(e) => setIncludePortfolio(e.target.checked)}
                    />
                    <span>Include Portfolio Building Steps</span>
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={includeInterview}
                      onChange={(e) => setIncludeInterview(e.target.checked)}
                    />
                    <span>Include Interview Preparation Steps</span>
                  </label>
                </div>
              </div>

              {error && <div className="error-banner">{error}</div>}

              <button
                type="submit"
                className="submit-button"
                disabled={isLoading || !careerName.trim()}
              >
                {isLoading ? 'Loading...' : 'Get Coaching Plan'}
              </button>
            </form>
          ) : (
            <div className="results-container">
              <div className="results-header">
                <h2 className="section-title">
                  Coaching Plan for {results.career.name}
                </h2>
                <button
                  className="back-button"
                  onClick={() => {
                    setResults(null);
                    setError('');
                  }}
                >
                  New Plan
                </button>
              </div>

              {/* Next Actions Today */}
              {results.next_actions_today && results.next_actions_today.length > 0 && (
                <div className="coach-section">
                  <h3 className="subsection-title">Next Actions Today</h3>
                  <div className="actions-list">
                    {results.next_actions_today.map((action, index) => (
                      <div key={index} className="action-card">
                        <div className="action-header">
                          <span className="action-number">{index + 1}</span>
                          <span className={`priority-badge priority-${action.priority}`}>
                            {action.priority}
                          </span>
                        </div>
                        <h4 className="action-title">{action.action}</h4>
                        <p className="action-description">{action.description}</p>
                        <div className="action-meta">
                          <span className="time-estimate">⏱ {action.estimated_time}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Seven Day Plan */}
              {results.seven_day_plan && results.seven_day_plan.length > 0 && (
                <div className="coach-section">
                  <h3 className="subsection-title">Seven Day Plan</h3>
                  <div className="seven-day-plan">
                    {results.seven_day_plan.map((day) => (
                      <div key={day.day} className="day-card">
                        <div className="day-header">
                          <h4 className="day-title">Day {day.day}</h4>
                          <span className="day-date">{day.date}</span>
                        </div>
                        <div className="day-focus">
                          <strong>Focus:</strong> {day.focus}
                        </div>
                        <div className="day-tasks">
                          <h5 className="tasks-title">Tasks:</h5>
                          <ul className="tasks-list">
                            {day.tasks.map((task, idx) => (
                              <li key={idx} className="task-item">
                                <span className="task-text">{task.task}</span>
                                <span className="task-time">{task.time_estimate}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div className="day-milestone">
                          <strong>Milestone:</strong> {day.milestone}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Learning Roadmap */}
              {results.learning_roadmap && (
                <div className="coach-section">
                  <h3 className="subsection-title">
                    Learning Roadmap ({results.learning_roadmap.duration_weeks} weeks)
                  </h3>
                  {results.learning_roadmap.overview && (
                    <p className="roadmap-overview">{results.learning_roadmap.overview}</p>
                  )}
                  <div className="roadmap-weeks">
                    {results.learning_roadmap.weeks.map((week) => (
                      <div key={week.week} className="week-card">
                        <div className="week-header">
                          <h4 className="week-title">Week {week.week}: {week.theme}</h4>
                        </div>
                        <div className="week-content">
                          {week.learning_objectives && week.learning_objectives.length > 0 && (
                            <div className="week-section">
                              <h5 className="week-section-title">Learning Objectives</h5>
                              <ul className="week-list">
                                {week.learning_objectives.map((obj, idx) => (
                                  <li key={idx}>{obj}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {week.key_activities && week.key_activities.length > 0 && (
                            <div className="week-section">
                              <h5 className="week-section-title">Key Activities</h5>
                              <ul className="week-list">
                                {week.key_activities.map((activity, idx) => (
                                  <li key={idx}>{activity}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {week.resources && week.resources.length > 0 && (
                            <div className="week-section">
                              <h5 className="week-section-title">Resources</h5>
                              <ul className="resources-list">
                                {week.resources.map((resource, idx) => (
                                  <li key={idx} className="resource-item">
                                    <span className="resource-name">{resource.name}</span>
                                    <span className="resource-type">({resource.type})</span>
                                    {resource.description && (
                                      <p className="resource-description">{resource.description}</p>
                                    )}
                                    {resource.url && (
                                      <a href={resource.url} target="_blank" rel="noopener noreferrer" className="resource-link">
                                        View Resource →
                                      </a>
                                    )}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {week.milestones && week.milestones.length > 0 && (
                            <div className="week-section">
                              <h5 className="week-section-title">Milestones</h5>
                              <ul className="week-list">
                                {week.milestones.map((milestone, idx) => (
                                  <li key={idx}>{milestone}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Portfolio Steps */}
              {results.portfolio_steps && results.portfolio_steps.length > 0 && (
                <div className="coach-section">
                  <h3 className="subsection-title">Portfolio Building Steps</h3>
                  <div className="steps-list">
                    {results.portfolio_steps.map((step) => (
                      <div key={step.step} className="step-card">
                        <div className="step-header">
                          <span className="step-number">Step {step.step}</span>
                          <span className="step-time">⏱ {step.estimated_time}</span>
                        </div>
                        <h4 className="step-title">{step.title}</h4>
                        <p className="step-description">{step.description}</p>
                        {step.purpose && (
                          <p className="step-purpose"><strong>Purpose:</strong> {step.purpose}</p>
                        )}
                        {step.tips && step.tips.length > 0 && (
                          <div className="step-tips">
                            <h5 className="tips-title">Tips:</h5>
                            <ul className="tips-list">
                              {step.tips.map((tip, idx) => (
                                <li key={idx}>{tip}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Interview Steps */}
              {results.interview_steps && results.interview_steps.length > 0 && (
                <div className="coach-section">
                  <h3 className="subsection-title">Interview Preparation Steps</h3>
                  <div className="steps-list">
                    {results.interview_steps.map((step) => (
                      <div key={step.step} className="step-card">
                        <div className="step-header">
                          <span className="step-number">Step {step.step}</span>
                          <span className="step-time">⏱ {step.estimated_time}</span>
                        </div>
                        <h4 className="step-title">{step.title}</h4>
                        <p className="step-description">{step.description}</p>
                        {step.focus_areas && step.focus_areas.length > 0 && (
                          <div className="step-focus">
                            <h5 className="focus-title">Focus Areas:</h5>
                            <ul className="focus-list">
                              {step.focus_areas.map((area, idx) => (
                                <li key={idx}>{area}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {step.practice_methods && step.practice_methods.length > 0 && (
                          <div className="step-practice">
                            <h5 className="practice-title">Practice Methods:</h5>
                            <ul className="practice-list">
                              {step.practice_methods.map((method, idx) => (
                                <li key={idx}>{method}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CoachPage;

