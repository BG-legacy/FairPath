import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './CareerSwitchPage.css';
import careerSwitchService, { CareerSwitchFormatted } from '../services/careerSwitch';
import dataService from '../services/data';

interface Particle {
  x: number;
  y: number;
  size: number;
  opacity: number;
  speed: number;
}

function CareerSwitchPage(): JSX.Element {
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Career input state - simple text inputs
  const [sourceCareer, setSourceCareer] = useState<string>('');
  const [targetCareer, setTargetCareer] = useState<string>('');

  // Results state
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [results, setResults] = useState<CareerSwitchFormatted | null>(null);

  // Handle form submission - use career names directly with OpenAI
  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    setResults(null);

    if (!sourceCareer.trim() || !targetCareer.trim()) {
      setError('Please enter both source and target career names');
      setIsLoading(false);
      return;
    }

    if (sourceCareer.trim().toLowerCase() === targetCareer.trim().toLowerCase()) {
      setError('Source and target careers must be different');
      setIsLoading(false);
      return;
    }

    try {
      // Use career names directly - no searching or matching
      const response = await careerSwitchService.getCareerSwitchByName({
        source_career_name: sourceCareer.trim(),
        target_career_name: targetCareer.trim(),
      });
      
      setResults(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze career switch');
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

  const getDifficultyColor = (difficulty: string): string => {
    switch (difficulty) {
      case 'Low':
        return '#4ade80';
      case 'Medium':
        return '#fbbf24';
      case 'High':
        return '#f87171';
      default:
        return '#ffffff';
    }
  };

  return (
    <div className="career-switch-page">
      <canvas ref={canvasRef} className="particles-canvas" />
      <div className="career-switch-container">
        <button className="back-button" onClick={() => navigate('/')}>
          ← Back to Home
        </button>

        <div className="career-switch-content">
          <h1 className="career-switch-title">Career Switch Analysis</h1>

          {!results ? (
            <form className="career-switch-form" onSubmit={handleSubmit}>
              {/* Source Career Input */}
              <div className="form-section">
                <label className="form-label">Source Career (Current)</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g., Business Analyst, Software Engineer, Teacher..."
                  value={sourceCareer}
                  onChange={(e) => setSourceCareer(e.target.value)}
                  disabled={isLoading}
                />
                <div style={{ marginTop: '4px', fontSize: '12px', color: '#888' }}>
                  Just type the career name - we'll find the best match automatically
                </div>
              </div>

              {/* Target Career Input */}
              <div className="form-section">
                <label className="form-label">Target Career (Desired)</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g., Data Scientist, Product Manager, Consultant..."
                  value={targetCareer}
                  onChange={(e) => setTargetCareer(e.target.value)}
                  disabled={isLoading}
                />
                <div style={{ marginTop: '4px', fontSize: '12px', color: '#888' }}>
                  Just type the career name - we'll find the best match automatically
                </div>
              </div>

              {error && <div className="error-banner">{error}</div>}

              <button
                type="submit"
                className="submit-button"
                disabled={isLoading || !sourceCareer.trim() || !targetCareer.trim()}
              >
                {isLoading ? 'Finding careers and analyzing...' : 'Analyze Career Switch'}
              </button>
            </form>
          ) : (
            <div className="results-container">
              <div className="results-header">
                <h2 className="section-title">Analysis Results</h2>
                <button
                  className="back-button"
                  onClick={() => {
                    setResults(null);
                    setError('');
                  }}
                >
                  New Analysis
                </button>
              </div>

              {/* Career Names */}
              <div className="careers-comparison">
                <div className="career-box">
                  <h3 className="career-box-title">From</h3>
                  <div className="career-box-name">{results.source_career.name}</div>
                  {results.source_career.soc_code && (
                    <div className="career-box-soc">SOC: {results.source_career.soc_code}</div>
                  )}
                </div>
                <div className="career-arrow">→</div>
                <div className="career-box">
                  <h3 className="career-box-title">To</h3>
                  <div className="career-box-name">{results.target_career.name}</div>
                  {results.target_career.soc_code && (
                    <div className="career-box-soc">SOC: {results.target_career.soc_code}</div>
                  )}
                </div>
              </div>

              {/* Overlap Percentage Visualization */}
              <div className="analysis-section">
                <h3 className="subsection-title">Skill Overlap</h3>
                <div className="overlap-visualization">
                  <div className="overlap-circle-container">
                    <div className="overlap-circle">
                      <div className="overlap-percentage">{results.overlap_percentage.toFixed(1)}%</div>
                      <div className="overlap-label">Overlap</div>
                    </div>
                  </div>
                  <div className="overlap-description">
                    {results.overlap_percentage >= 70
                      ? 'High skill overlap - many skills transfer directly'
                      : results.overlap_percentage >= 40
                      ? 'Moderate skill overlap - some skills transfer, some need learning'
                      : 'Low skill overlap - significant learning required'}
                  </div>
                </div>
              </div>

              {/* Difficulty Classification */}
              <div className="analysis-section">
                <h3 className="subsection-title">Transition Difficulty</h3>
                <div
                  className="difficulty-badge"
                  style={{ backgroundColor: getDifficultyColor(results.difficulty) }}
                >
                  {results.difficulty}
                </div>
              </div>

              {/* Transition Time Range */}
              <div className="analysis-section">
                <h3 className="subsection-title">Estimated Transition Time</h3>
                <div className="time-range">
                  <div className="time-range-value">
                    {results.transition_time_range.min_months} - {results.transition_time_range.max_months} months
                  </div>
                  <div className="time-range-note">{results.transition_time_range.range}</div>
                  {results.transition_time_range.note && (
                    <div className="time-range-note-small">{results.transition_time_range.note}</div>
                  )}
                </div>
              </div>

              {/* Skill Translation Map */}
              <div className="analysis-section">
                <h3 className="subsection-title">Skill Translation Map</h3>
                <div className="skill-map">
                  <div className="skill-category">
                    <h4 className="skill-category-title">Transfers Directly</h4>
                    {results.skill_translation_map.transfers_directly.length > 0 ? (
                      <ul className="skill-list">
                        {results.skill_translation_map.transfers_directly.map((skillItem, idx) => (
                          <li key={idx} className="skill-item transfer">
                            {skillItem.skill}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="no-skills">No skills transfer directly</p>
                    )}
                  </div>
                  <div className="skill-category">
                    <h4 className="skill-category-title">Needs Learning</h4>
                    {results.skill_translation_map.needs_learning.length > 0 ? (
                      <ul className="skill-list">
                        {results.skill_translation_map.needs_learning.map((skillItem, idx) => (
                          <li key={idx} className="skill-item learning">
                            {skillItem.skill}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="no-skills">No new skills required</p>
                    )}
                  </div>
                  <div className="skill-category">
                    <h4 className="skill-category-title">Optional Skills</h4>
                    {results.skill_translation_map.optional_skills.length > 0 ? (
                      <ul className="skill-list">
                        {results.skill_translation_map.optional_skills.map((skillItem, idx) => (
                          <li key={idx} className="skill-item optional">
                            {skillItem.skill}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="no-skills">No optional skills identified</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Success Factors */}
              <div className="analysis-section">
                <h3 className="subsection-title">Success Factors</h3>
                <ul className="factors-list">
                  {results.success_factors.map((factorItem, idx) => (
                    <li key={idx} className="factor-item success">
                      <div className="factor-name">✓ {factorItem.factor}</div>
                      <div className="factor-description">{factorItem.description}</div>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Risk Factors */}
              <div className="analysis-section">
                <h3 className="subsection-title">Risk Factors</h3>
                <ul className="factors-list">
                  {results.risk_factors.map((factorItem, idx) => (
                    <li key={idx} className="factor-item risk">
                      <div className="factor-name">⚠ {factorItem.factor}</div>
                      <div className="factor-description">{factorItem.description}</div>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Overall Assessment */}
              {results.overall_assessment && (
                <div className="analysis-section">
                  <h3 className="subsection-title">Overall Assessment</h3>
                  <div className="overall-assessment">{results.overall_assessment}</div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CareerSwitchPage;

