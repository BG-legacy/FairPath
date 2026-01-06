import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import './PathsPage.css';
import pathsService, { EducationPathways } from '../services/paths';
import dataService, { OccupationCatalog } from '../services/data';

interface Particle {
  x: number;
  y: number;
  size: number;
  opacity: number;
  speed: number;
}

function PathsPage(): JSX.Element {
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
  const [results, setResults] = useState<EducationPathways | null>(null);

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

      // Then load the pathways data
      const response = await pathsService.getEducationPathways(id);
      setResults(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get education pathways');
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
    navigate(`/paths/${career.occupation.career_id}`);
  };

  // Handle form submission - navigate to route with careerId
  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();

    if (!careerId) {
      setError('Please select a career');
      return;
    }

    navigate(`/paths/${careerId}`);
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

  const formatCurrency = (amount: number, currency: string): string => {
    if (currency === 'USD' || currency === 'usd') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(amount);
    }
    return `${amount} ${currency}`;
  };

  const formatMonths = (months: number): string => {
    if (months < 12) {
      return `${months} month${months !== 1 ? 's' : ''}`;
    }
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;
    if (remainingMonths === 0) {
      return `${years} year${years !== 1 ? 's' : ''}`;
    }
    return `${years} year${years !== 1 ? 's' : ''} ${remainingMonths} month${remainingMonths !== 1 ? 's' : ''}`;
  };

  return (
    <div className="paths-page">
      <canvas ref={canvasRef} className="particles-canvas" />
      <div className="paths-container">
        <button className="back-button" onClick={() => navigate('/')}>
          ← Back to Home
        </button>

        <div className="paths-content">
          <h1 className="paths-title">Education Pathways</h1>

          {!results ? (
            <form className="paths-form" onSubmit={handleSubmit}>
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
                {isLoading ? 'Loading Pathways...' : 'Get Education Pathways'}
              </button>
            </form>
          ) : (
            <div className="results-container">
              <div className="results-header">
                <h2 className="section-title">Education Pathways</h2>
                <button
                  className="back-button"
                  onClick={() => {
                    setResults(null);
                    setError('');
                  }}
                >
                  New Search
                </button>
              </div>

              {/* Career Info */}
              <div className="career-info">
                <h3 className="career-name">{results.career.name}</h3>
                {results.career.soc_code && (
                  <div className="career-soc">SOC: {results.career.soc_code}</div>
                )}
              </div>

              {/* Pathways Display */}
              {results.pathways && results.pathways.length > 0 ? (
                <div className="pathways-grid">
                  {results.pathways.map((pathway, idx) => (
                    <div key={idx} className="pathway-card">
                      <h3 className="pathway-name">{pathway.name}</h3>
                      
                      {/* Description */}
                      {pathway.description && (
                        <div className="pathway-description">{pathway.description}</div>
                      )}

                      {/* Cost Range */}
                      <div className="pathway-section">
                        <h4 className="pathway-section-title">Cost Range</h4>
                        <div className="cost-range">
                          <div className="cost-value">
                            {formatCurrency(pathway.cost_range.min, pathway.cost_range.currency)} -{' '}
                            {formatCurrency(pathway.cost_range.max, pathway.cost_range.currency)}
                          </div>
                          {pathway.cost_range.description && (
                            <div className="cost-description">{pathway.cost_range.description}</div>
                          )}
                        </div>
                      </div>

                      {/* Time Range */}
                      <div className="pathway-section">
                        <h4 className="pathway-section-title">Time Range</h4>
                        <div className="time-range">
                          <div className="time-value">
                            {formatMonths(pathway.time_range.min_months)} -{' '}
                            {formatMonths(pathway.time_range.max_months)}
                          </div>
                          {pathway.time_range.description && (
                            <div className="time-description">{pathway.time_range.description}</div>
                          )}
                        </div>
                      </div>

                      {/* Pros */}
                      {pathway.pros && pathway.pros.length > 0 && (
                        <div className="pathway-section">
                          <h4 className="pathway-section-title">Pros</h4>
                          <ul className="pros-list">
                            {pathway.pros.map((pro, proIdx) => (
                              <li key={proIdx} className="pro-item">
                                ✓ {pro}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Tradeoffs */}
                      {pathway.tradeoffs && pathway.tradeoffs.length > 0 && (
                        <div className="pathway-section">
                          <h4 className="pathway-section-title">Tradeoffs</h4>
                          <ul className="tradeoffs-list">
                            {pathway.tradeoffs.map((tradeoff, tradeoffIdx) => (
                              <li key={tradeoffIdx} className="tradeoff-item">
                                ⚠ {tradeoff}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-pathways">
                  <p>No education pathways available for this career.</p>
                </div>
              )}

              {/* Availability Notice */}
              {!results.available && (
                <div className="availability-notice">
                  <p>Note: Limited pathway information available for this career.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PathsPage;

