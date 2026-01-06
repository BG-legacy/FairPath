import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import './OutlookPage.css';
import outlookService, { CareerOutlook } from '../services/outlook';
import dataService, { OccupationCatalog } from '../services/data';

interface Particle {
  x: number;
  y: number;
  size: number;
  opacity: number;
  speed: number;
}

function OutlookPage(): JSX.Element {
  const { careerId: routeCareerId } = useParams<{ careerId: string }>();
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Career selection state
  const [careerId, setCareerId] = useState<string>(routeCareerId || '');
  const [careerSearch, setCareerSearch] = useState<string>('');
  const [careerResults, setCareerResults] = useState<OccupationCatalog[]>([]);
  const [showResults, setShowResults] = useState<boolean>(false);

  // Results state
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [results, setResults] = useState<CareerOutlook | null>(null);
  const [selectedCareer, setSelectedCareer] = useState<OccupationCatalog | null>(null);

  // Search for careers
  const searchCareers = useCallback(async (query: string): Promise<void> => {
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
  }, []);

  // Handle search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      searchCareers(careerSearch);
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [careerSearch, searchCareers]);

  // Load career data
  const loadCareerData = useCallback(async (id: string): Promise<void> => {
    setError('');
    setIsLoading(true);
    setResults(null);

    try {
      // First, get the career details to set the search text
      const careerData = await dataService.getOccupationById(id);
      setCareerSearch(careerData.occupation.name);
      setSelectedCareer(careerData);

      // Then load the outlook data
      const response = await outlookService.getCareerOutlook(id);
      setResults(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get career outlook');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load data when routeCareerId changes
  useEffect(() => {
    if (routeCareerId) {
      setCareerId(routeCareerId);
      loadCareerData(routeCareerId);
    }
  }, [routeCareerId, loadCareerData]);

  // Select career and navigate
  const selectCareer = (career: OccupationCatalog): void => {
    navigate(`/outlook/${career.occupation.career_id}`);
  };

  // Handle form submission - navigate to route with careerId
  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();

    if (!careerId) {
      setError('Please select a career');
      return;
    }

    navigate(`/outlook/${careerId}`);
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

  const getOutlookColor = (outlook: string): string => {
    switch (outlook) {
      case 'Strong':
        return '#4ade80';
      case 'Moderate':
        return '#fbbf24';
      case 'Declining':
        return '#f87171';
      case 'Uncertain':
        return '#94a3b8';
      default:
        return '#ffffff';
    }
  };

  const getRiskColor = (risk: string): string => {
    switch (risk) {
      case 'Low':
        return '#4ade80';
      case 'Medium':
        return '#fbbf24';
      case 'High':
        return '#f87171';
      case 'Uncertain':
        return '#94a3b8';
      default:
        return '#ffffff';
    }
  };

  const getStabilityColor = (signal: string): string => {
    switch (signal) {
      case 'Expanding':
        return '#4ade80';
      case 'Shifting':
        return '#fbbf24';
      case 'Declining':
        return '#f87171';
      case 'Uncertain':
        return '#94a3b8';
      default:
        return '#ffffff';
    }
  };

  const getConfidenceColor = (level: string): string => {
    switch (level) {
      case 'High':
        return '#4ade80';
      case 'Medium':
        return '#fbbf24';
      case 'Low':
        return '#f87171';
      default:
        return '#ffffff';
    }
  };

  return (
    <div className="outlook-page">
      <canvas ref={canvasRef} className="particles-canvas" />
      <div className="outlook-container">
        <button className="back-button" onClick={() => navigate('/')}>
          ← Back to Home
        </button>

        <div className="outlook-content">
          <h1 className="outlook-title">Career Outlook Analysis</h1>

          {!results ? (
            <form className="outlook-form" onSubmit={handleSubmit}>
              {/* Career Selector */}
              <div className="form-section">
                <label className="form-label">Career</label>
                <div className="career-selector-container">
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Search for a career..."
                    value={careerSearch}
                    onChange={(e) => {
                      setCareerSearch(e.target.value);
                      setCareerId('');
                      setSelectedCareer(null);
                    }}
                    onFocus={() => {
                      if (careerSearch) {
                        setShowResults(true);
                      }
                    }}
                  />
                  {showResults && careerResults.length > 0 && (
                    <div className="career-results-dropdown">
                      {careerResults.map((career) => (
                        <div
                          key={career.occupation.career_id}
                          className="career-result-item"
                          onClick={() => selectCareer(career)}
                        >
                          <div className="career-result-name">{career.occupation.name}</div>
                          <div className="career-result-soc">SOC: {career.occupation.soc_code}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {error && <div className="error-banner">{error}</div>}

              <button
                type="submit"
                className="submit-button"
                disabled={isLoading || !careerId}
              >
                {isLoading ? 'Analyzing...' : 'Get Outlook'}
              </button>
            </form>
          ) : (
            <div className="results-container">
              <div className="results-header">
                <h2 className="section-title">Outlook Results</h2>
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

              {/* Career Name */}
              {selectedCareer && (
                <div className="career-info">
                  <h3 className="career-name">{selectedCareer.occupation.name}</h3>
                  <div className="career-soc">SOC: {selectedCareer.occupation.soc_code}</div>
                </div>
              )}

              {/* Growth Outlook */}
              <div className="analysis-section">
                <h3 className="subsection-title">Growth Outlook</h3>
                <div className="outlook-badge-container">
                  <div
                    className="outlook-badge"
                    style={{ backgroundColor: getOutlookColor(results.growth_outlook.outlook) }}
                  >
                    {results.growth_outlook.outlook}
                  </div>
                  <div className="confidence-indicator">
                    <span className="confidence-label">Confidence:</span>
                    <span
                      className="confidence-badge"
                      style={{ backgroundColor: getConfidenceColor(results.growth_outlook.confidence) }}
                    >
                      {results.growth_outlook.confidence}
                    </span>
                  </div>
                </div>
                {results.growth_outlook.range && (
                  <div className="outlook-range">
                    {results.growth_outlook.range.growth_rate_percent !== undefined && (
                      <div className="range-item">
                        <span className="range-label">Growth Rate:</span>
                        <span className="range-value">
                          {results.growth_outlook.range.growth_rate_percent > 0 ? '+' : ''}
                          {results.growth_outlook.range.growth_rate_percent.toFixed(1)}%
                        </span>
                      </div>
                    )}
                    {results.growth_outlook.range.employment_2024 !== undefined && (
                      <div className="range-item">
                        <span className="range-label">Employment 2024:</span>
                        <span className="range-value">
                          {results.growth_outlook.range.employment_2024.toLocaleString()}
                        </span>
                      </div>
                    )}
                    {results.growth_outlook.range.employment_2034 !== undefined && (
                      <div className="range-item">
                        <span className="range-label">Employment 2034:</span>
                        <span className="range-value">
                          {results.growth_outlook.range.employment_2034.toLocaleString()}
                        </span>
                      </div>
                    )}
                    {results.growth_outlook.range.annual_openings !== undefined && (
                      <div className="range-item">
                        <span className="range-label">Annual Openings:</span>
                        <span className="range-value">
                          {results.growth_outlook.range.annual_openings.toLocaleString()}
                        </span>
                      </div>
                    )}
                  </div>
                )}
                <div className="reasoning-box">
                  <h4 className="reasoning-title">Reasoning</h4>
                  <p className="reasoning-text">{results.growth_outlook.reasoning}</p>
                </div>
              </div>

              {/* Automation Risk */}
              <div className="analysis-section">
                <h3 className="subsection-title">Automation Risk</h3>
                <div className="outlook-badge-container">
                  <div
                    className="outlook-badge"
                    style={{ backgroundColor: getRiskColor(results.automation_risk.risk) }}
                  >
                    {results.automation_risk.risk}
                  </div>
                  <div className="confidence-indicator">
                    <span className="confidence-label">Confidence:</span>
                    <span
                      className="confidence-badge"
                      style={{ backgroundColor: getConfidenceColor(results.automation_risk.confidence) }}
                    >
                      {results.automation_risk.confidence}
                    </span>
                  </div>
                </div>
                <div className="reasoning-box">
                  <h4 className="reasoning-title">Reasoning</h4>
                  <p className="reasoning-text">{results.automation_risk.reasoning}</p>
                </div>
              </div>

              {/* Stability Signal */}
              <div className="analysis-section">
                <h3 className="subsection-title">Stability Signal</h3>
                <div className="outlook-badge-container">
                  <div
                    className="outlook-badge"
                    style={{ backgroundColor: getStabilityColor(results.stability.signal) }}
                  >
                    {results.stability.signal}
                  </div>
                  <div className="confidence-indicator">
                    <span className="confidence-label">Confidence:</span>
                    <span
                      className="confidence-badge"
                      style={{ backgroundColor: getConfidenceColor(results.stability.confidence) }}
                    >
                      {results.stability.confidence}
                    </span>
                  </div>
                </div>
                <div className="reasoning-box">
                  <h4 className="reasoning-title">Reasoning</h4>
                  <p className="reasoning-text">{results.stability.reasoning}</p>
                </div>
              </div>

              {/* Overall Confidence */}
              <div className="analysis-section">
                <h3 className="subsection-title">Overall Confidence</h3>
                <div className="confidence-section">
                  <div
                    className="confidence-badge-large"
                    style={{ backgroundColor: getConfidenceColor(results.confidence.level) }}
                  >
                    {results.confidence.level}
                  </div>
                  {results.confidence.reasoning && (
                    <p className="confidence-reasoning">{results.confidence.reasoning}</p>
                  )}
                  {results.confidence.factors && results.confidence.factors.length > 0 && (
                    <div className="confidence-factors">
                      <h4 className="factors-title">Key Factors:</h4>
                      <ul className="factors-list">
                        {results.confidence.factors.map((factor, idx) => (
                          <li key={idx} className="factor-item">{factor}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {/* Assumptions and Limitations */}
              <div className="analysis-section">
                <h3 className="subsection-title">Assumptions and Limitations</h3>
                <div className="assumptions-section">
                  {results.assumptions.assumptions && results.assumptions.assumptions.length > 0 && (
                    <div className="assumptions-box">
                      <h4 className="assumptions-title">Assumptions</h4>
                      <ul className="assumptions-list">
                        {results.assumptions.assumptions.map((assumption, idx) => (
                          <li key={idx} className="assumption-item">{assumption}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {results.assumptions.limitations && results.assumptions.limitations.length > 0 && (
                    <div className="limitations-box">
                      <h4 className="limitations-title">Limitations</h4>
                      <ul className="limitations-list">
                        {results.assumptions.limitations.map((limitation, idx) => (
                          <li key={idx} className="limitation-item">{limitation}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {results.assumptions.data_sources && results.assumptions.data_sources.length > 0 && (
                    <div className="data-sources-box">
                      <h4 className="data-sources-title">Data Sources</h4>
                      <ul className="data-sources-list">
                        {results.assumptions.data_sources.map((source, idx) => (
                          <li key={idx} className="data-source-item">{source}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {results.assumptions.methodology && (
                    <div className="methodology-box">
                      <h4 className="methodology-title">Methodology</h4>
                      <p className="methodology-text">{results.assumptions.methodology}</p>
                    </div>
                  )}
                </div>
                <div className="assumptions-link">
                  <a
                    href="/api/outlook/assumptions"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="link-button"
                  >
                    View Full Assumptions Documentation
                  </a>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default OutlookPage;

