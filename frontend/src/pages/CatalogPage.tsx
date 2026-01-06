import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './CatalogPage.css';
import dataService, { OccupationCatalog, CatalogQueryParams } from '../services/data';

interface Particle {
  x: number;
  y: number;
  size: number;
  opacity: number;
  speed: number;
}

function CatalogPage(): JSX.Element {
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // State
  const [occupations, setOccupations] = useState<OccupationCatalog[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [selectedOccupation, setSelectedOccupation] = useState<OccupationCatalog | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  // Filters and pagination
  const [searchText, setSearchText] = useState<string>('');
  const [socCode, setSocCode] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const itemsPerPage = 12;

  // Load occupations
  const loadOccupations = async (page: number = 1): Promise<void> => {
    setIsLoading(true);
    setError('');

    try {
      const params: CatalogQueryParams = {
        limit: itemsPerPage,
        offset: (page - 1) * itemsPerPage,
      };

      if (searchText.trim()) {
        params.search = searchText.trim();
      }

      if (socCode.trim()) {
        params.soc_code = socCode.trim();
      }

      const response = await dataService.getOccupationCatalog(params);
      // Sort results alphabetically by occupation name
      const sortedOccupations = [...response.occupations].sort((a, b) =>
        a.occupation.name.localeCompare(b.occupation.name)
      );
      setOccupations(sortedOccupations);
      setTotal(response.total);
      setTotalPages(Math.ceil(response.total / itemsPerPage));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load occupations');
      setOccupations([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadOccupations(currentPage);
  }, [currentPage]);

  // Handle search
  const handleSearch = (): void => {
    setCurrentPage(1);
    loadOccupations(1);
  };

  // Handle filter changes
  const handleFilterChange = (): void => {
    setCurrentPage(1);
    loadOccupations(1);
  };

  // Handle pagination
  const handlePageChange = (page: number): void => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Handle occupation click - navigate to detail page
  const handleOccupationClick = (careerId: string): void => {
    navigate(`/catalog/${careerId}`);
  };

  // Close modal
  const closeModal = (): void => {
    setIsModalOpen(false);
    setSelectedOccupation(null);
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

  return (
    <div className="catalog-page">
      <canvas ref={canvasRef} className="particles-canvas" />
      <div className="catalog-container">
        <button className="back-button" onClick={() => navigate('/')}>
          ← Back to Home
        </button>

        <div className="catalog-content">
          <h1 className="catalog-title">Occupation Catalog</h1>

          {/* Filters */}
          <div className="filters-section">
            <div className="filter-row">
              <div className="filter-group">
                <label className="form-label">Search</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Search by name or description..."
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleSearch();
                    }
                  }}
                />
              </div>
              <div className="filter-group">
                <label className="form-label">SOC Code</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g., 11-1011.00"
                  value={socCode}
                  onChange={(e) => setSocCode(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleFilterChange();
                    }
                  }}
                />
              </div>
              <div className="filter-actions">
                <button
                  className="filter-button"
                  onClick={handleSearch}
                  disabled={isLoading}
                >
                  Search
                </button>
                <button
                  className="filter-button secondary"
                  onClick={() => {
                    setSearchText('');
                    setSocCode('');
                    setCurrentPage(1);
                    loadOccupations(1);
                  }}
                  disabled={isLoading}
                >
                  Clear
                </button>
              </div>
            </div>
          </div>

          {/* Results info */}
          {!isLoading && (
            <div className="results-info">
              <span>
                Showing {occupations.length} of {total} occupations
              </span>
            </div>
          )}

          {/* Error */}
          {error && <div className="error-banner">{error}</div>}

          {/* Loading */}
          {isLoading && (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading occupations...</p>
            </div>
          )}

          {/* Occupations grid */}
          {!isLoading && occupations.length > 0 && (
            <>
              <div className="occupations-grid">
                {occupations.map((occupation) => (
                  <div
                    key={occupation.occupation.career_id}
                    className="occupation-card"
                    onClick={() => handleOccupationClick(occupation.occupation.career_id)}
                  >
                    <div className="occupation-header">
                      <h3 className="occupation-name">{occupation.occupation.name}</h3>
                      {occupation.occupation.soc_code && (
                        <span className="soc-badge">{occupation.occupation.soc_code}</span>
                      )}
                    </div>
                    <p className="occupation-description">
                      {occupation.occupation.description.length > 150
                        ? `${occupation.occupation.description.substring(0, 150)}...`
                        : occupation.occupation.description}
                    </p>
                    <div className="occupation-stats">
                      {occupation.skills.length > 0 && (
                        <div className="stat-item">
                          <span className="stat-label">Skills:</span>
                          <span className="stat-value">{occupation.skills.length}</span>
                        </div>
                      )}
                      {occupation.tasks.length > 0 && (
                        <div className="stat-item">
                          <span className="stat-label">Tasks:</span>
                          <span className="stat-value">{occupation.tasks.length}</span>
                        </div>
                      )}
                      {occupation.bls_projection && (
                        <div className="stat-item">
                          <span className="stat-label">BLS Data:</span>
                          <span className="stat-value">Available</span>
                        </div>
                      )}
                    </div>
                    {occupation.bls_projection?.median_wage_2024 && (
                      <div className="occupation-wage">
                        <span className="wage-label">Median Wage:</span>
                        <span className="wage-value">
                          ${occupation.bls_projection.median_wage_2024.toLocaleString()}/year
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="pagination">
                  <button
                    className="pagination-button"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1 || isLoading}
                  >
                    Previous
                  </button>
                  <div className="pagination-info">
                    Page {currentPage} of {totalPages}
                  </div>
                  <button
                    className="pagination-button"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages || isLoading}
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}

          {/* No results */}
          {!isLoading && occupations.length === 0 && !error && (
            <div className="no-results">
              <p>No occupations found. Try adjusting your search or filters.</p>
            </div>
          )}
        </div>
      </div>

      {/* Detail Modal */}
      {isModalOpen && selectedOccupation && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={closeModal}>
              ×
            </button>
            <div className="modal-header">
              <h2 className="modal-title">{selectedOccupation.occupation.name}</h2>
              {selectedOccupation.occupation.soc_code && (
                <span className="modal-soc">{selectedOccupation.occupation.soc_code}</span>
              )}
            </div>

            <div className="modal-body">
              {/* Description */}
              <div className="modal-section">
                <h3 className="modal-section-title">Description</h3>
                <p className="modal-text">{selectedOccupation.occupation.description}</p>
              </div>

              {/* BLS Projections */}
              {selectedOccupation.bls_projection && (
                <div className="modal-section">
                  <h3 className="modal-section-title">BLS Employment Projections</h3>
                  <div className="bls-grid">
                    {selectedOccupation.bls_projection.employment_2024 && (
                      <div className="bls-item">
                        <span className="bls-label">Employment 2024:</span>
                        <span className="bls-value">
                          {selectedOccupation.bls_projection.employment_2024.toLocaleString()} (thousands)
                        </span>
                      </div>
                    )}
                    {selectedOccupation.bls_projection.employment_2034 && (
                      <div className="bls-item">
                        <span className="bls-label">Projected Employment 2034:</span>
                        <span className="bls-value">
                          {selectedOccupation.bls_projection.employment_2034.toLocaleString()} (thousands)
                        </span>
                      </div>
                    )}
                    {selectedOccupation.bls_projection.percent_change !== undefined && (
                      <div className="bls-item">
                        <span className="bls-label">Percent Change:</span>
                        <span className="bls-value">
                          {selectedOccupation.bls_projection.percent_change > 0 ? '+' : ''}
                          {selectedOccupation.bls_projection.percent_change.toFixed(1)}%
                        </span>
                      </div>
                    )}
                    {selectedOccupation.bls_projection.median_wage_2024 && (
                      <div className="bls-item">
                        <span className="bls-label">Median Wage 2024:</span>
                        <span className="bls-value">
                          ${selectedOccupation.bls_projection.median_wage_2024.toLocaleString()}/year
                        </span>
                      </div>
                    )}
                    {selectedOccupation.bls_projection.annual_openings && (
                      <div className="bls-item">
                        <span className="bls-label">Annual Openings:</span>
                        <span className="bls-value">
                          {selectedOccupation.bls_projection.annual_openings.toLocaleString()}
                        </span>
                      </div>
                    )}
                    {selectedOccupation.bls_projection.typical_education && (
                      <div className="bls-item">
                        <span className="bls-label">Typical Education:</span>
                        <span className="bls-value">
                          {selectedOccupation.bls_projection.typical_education}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Skills */}
              {selectedOccupation.skills.length > 0 && (
                <div className="modal-section">
                  <h3 className="modal-section-title">Skills ({selectedOccupation.skills.length})</h3>
                  <div className="skills-list-modal">
                    {selectedOccupation.skills
                      .sort((a, b) => (b.importance || 0) - (a.importance || 0))
                      .slice(0, 20)
                      .map((skill, index) => (
                        <div key={index} className="skill-item-modal">
                          <span className="skill-name-modal">{skill.skill_name}</span>
                          {skill.importance !== undefined && (
                            <span className="skill-importance">
                              Importance: {skill.importance.toFixed(1)}
                            </span>
                          )}
                          {skill.level !== undefined && (
                            <span className="skill-level">Level: {skill.level.toFixed(1)}</span>
                          )}
                        </div>
                      ))}
                    {selectedOccupation.skills.length > 20 && (
                      <p className="modal-note">
                        Showing top 20 skills by importance. Total: {selectedOccupation.skills.length}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Tasks */}
              {selectedOccupation.tasks.length > 0 && (
                <div className="modal-section">
                  <h3 className="modal-section-title">Tasks ({selectedOccupation.tasks.length})</h3>
                  <ul className="tasks-list">
                    {selectedOccupation.tasks.slice(0, 10).map((task, index) => (
                      <li key={index} className="task-item">
                        {task.task_description}
                      </li>
                    ))}
                    {selectedOccupation.tasks.length > 10 && (
                      <p className="modal-note">
                        Showing first 10 tasks. Total: {selectedOccupation.tasks.length}
                      </p>
                    )}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default CatalogPage;

