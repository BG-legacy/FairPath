import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import './CertsPage.css';
import certsService, { CareerCertifications, Certification } from '../services/certs';
import dataService, { OccupationCatalog } from '../services/data';

interface Particle {
  x: number;
  y: number;
  size: number;
  opacity: number;
  speed: number;
}

function CertsPage(): JSX.Element {
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
  const [results, setResults] = useState<CareerCertifications | null>(null);

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

      // Then load the certifications data
      const response = await certsService.getCertifications(id);
      setResults(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get certifications');
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
    navigate(`/certs/${career.occupation.career_id}`);
  };

  // Handle form submission - navigate to route with careerId
  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();

    if (!careerId) {
      setError('Please select a career');
      return;
    }

    navigate(`/certs/${careerId}`);
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

  const formatCost = (cost: number | { min?: number; max?: number } | undefined): string => {
    if (!cost) return 'Not specified';
    if (typeof cost === 'number') {
      return `$${cost.toLocaleString()}`;
    }
    if (cost.min && cost.max) {
      return `$${cost.min.toLocaleString()} - $${cost.max.toLocaleString()}`;
    }
    if (cost.min) {
      return `$${cost.min.toLocaleString()}+`;
    }
    if (cost.max) {
      return `Up to $${cost.max.toLocaleString()}`;
    }
    return 'Not specified';
  };

  return (
    <div className="certs-page">
      <canvas ref={canvasRef} className="particles-canvas" />
      <div className="certs-container">
        <button className="back-button" onClick={() => navigate('/')}>
          ← Back to Home
        </button>

        <div className="certs-content">
          <h1 className="certs-title">Career Certifications</h1>

          {!results ? (
            <form className="certs-form" onSubmit={handleSubmit}>
              {/* Career Selection */}
              <div className="form-section">
                <label className="form-label">Career</label>
                <div className="career-search-container">
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Search for a career..."
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
                    <span>Selected: {careerSearch}</span>
                  </div>
                )}
              </div>

              {error && <div className="error-banner">{error}</div>}

              <button
                type="submit"
                className="submit-button"
                disabled={isLoading || !careerId}
              >
                {isLoading ? 'Loading...' : 'Get Certifications'}
              </button>
            </form>
          ) : (
            <div className="results-container">
              <div className="results-header">
                <h2 className="section-title">
                  Certifications for {results.career.name}
                </h2>
                <button
                  className="back-button"
                  onClick={() => {
                    setResults(null);
                    setError('');
                    setCareerId('');
                    setCareerSearch('');
                  }}
                >
                  New Search
                </button>
              </div>

              {/* Entry-Level Certifications */}
              {results.entry_level && results.entry_level.length > 0 && (
                <div className="cert-section">
                  <h3 className="subsection-title">Entry-Level Certifications</h3>
                  <div className="certifications-grid">
                    {results.entry_level.map((cert: Certification, index: number) => (
                      <div key={index} className="cert-card">
                        <div className="cert-header">
                          <h4 className="cert-name">{cert.name}</h4>
                          {cert.issuer && (
                            <span className="cert-issuer">Issued by: {cert.issuer}</span>
                          )}
                        </div>
                        {cert.description && (
                          <p className="cert-description">{cert.description}</p>
                        )}
                        <div className="cert-details">
                          {cert.cost && (
                            <div className="cert-detail">
                              <span className="detail-label">Cost:</span>
                              <span className="detail-value">{formatCost(cert.cost)}</span>
                            </div>
                          )}
                          {cert.duration && (
                            <div className="cert-detail">
                              <span className="detail-label">Duration:</span>
                              <span className="detail-value">{cert.duration}</span>
                            </div>
                          )}
                          {cert.difficulty && (
                            <div className="cert-detail">
                              <span className="detail-label">Difficulty:</span>
                              <span className="detail-value">{cert.difficulty}</span>
                            </div>
                          )}
                          {cert.value && (
                            <div className="cert-detail">
                              <span className="detail-label">Value:</span>
                              <span className="detail-value">{cert.value}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Career-Advancing Certifications */}
              {results.career_advancing && results.career_advancing.length > 0 && (
                <div className="cert-section">
                  <h3 className="subsection-title">Career-Advancing Certifications</h3>
                  <div className="certifications-grid">
                    {results.career_advancing.map((cert: Certification, index: number) => (
                      <div key={index} className="cert-card">
                        <div className="cert-header">
                          <h4 className="cert-name">{cert.name}</h4>
                          {cert.issuer && (
                            <span className="cert-issuer">Issued by: {cert.issuer}</span>
                          )}
                        </div>
                        {cert.description && (
                          <p className="cert-description">{cert.description}</p>
                        )}
                        <div className="cert-details">
                          {cert.cost && (
                            <div className="cert-detail">
                              <span className="detail-label">Cost:</span>
                              <span className="detail-value">{formatCost(cert.cost)}</span>
                            </div>
                          )}
                          {cert.duration && (
                            <div className="cert-detail">
                              <span className="detail-label">Duration:</span>
                              <span className="detail-value">{cert.duration}</span>
                            </div>
                          )}
                          {cert.difficulty && (
                            <div className="cert-detail">
                              <span className="detail-label">Difficulty:</span>
                              <span className="detail-value">{cert.difficulty}</span>
                            </div>
                          )}
                          {cert.value && (
                            <div className="cert-detail">
                              <span className="detail-label">Value:</span>
                              <span className="detail-value">{cert.value}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Optional/Overhyped Certifications */}
              {results.optional_overhyped && results.optional_overhyped.length > 0 && (
                <div className="cert-section">
                  <h3 className="subsection-title">Optional/Overhyped Certifications</h3>
                  <div className="certifications-grid">
                    {results.optional_overhyped.map((cert: Certification, index: number) => (
                      <div key={index} className="cert-card optional">
                        <div className="cert-header">
                          <h4 className="cert-name">{cert.name}</h4>
                          {cert.issuer && (
                            <span className="cert-issuer">Issued by: {cert.issuer}</span>
                          )}
                        </div>
                        {cert.description && (
                          <p className="cert-description">{cert.description}</p>
                        )}
                        {cert.rationale && (
                          <div className="cert-rationale">
                            <h5 className="rationale-title">Rationale:</h5>
                            <p className="rationale-text">{cert.rationale}</p>
                          </div>
                        )}
                        <div className="cert-details">
                          {cert.cost && (
                            <div className="cert-detail">
                              <span className="detail-label">Cost:</span>
                              <span className="detail-value">{formatCost(cert.cost)}</span>
                            </div>
                          )}
                          {cert.duration && (
                            <div className="cert-detail">
                              <span className="detail-label">Duration:</span>
                              <span className="detail-value">{cert.duration}</span>
                            </div>
                          )}
                          {cert.difficulty && (
                            <div className="cert-detail">
                              <span className="detail-label">Difficulty:</span>
                              <span className="detail-value">{cert.difficulty}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {(!results.entry_level || results.entry_level.length === 0) &&
                (!results.career_advancing || results.career_advancing.length === 0) &&
                (!results.optional_overhyped || results.optional_overhyped.length === 0) && (
                  <div className="no-results">
                    <p>No certifications found for this career.</p>
                  </div>
                )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CertsPage;

