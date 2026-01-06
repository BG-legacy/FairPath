/**
 * CareerSelector Component
 * Searchable career selector component
 */
import { useState, useMemo, ChangeEvent } from 'react';
import { UseFormRegisterReturn, FieldError } from 'react-hook-form';
import { OccupationCatalog } from '../../services/data';
import './CareerSelector.css';

interface CareerSelectorProps {
  careers: OccupationCatalog[];
  selectedCareerId: string;
  onCareerChange: (careerId: string) => void;
  register?: UseFormRegisterReturn;
  error?: FieldError;
  placeholder?: string;
  showSearch?: boolean;
  required?: boolean;
}

export function CareerSelector({
  careers,
  selectedCareerId,
  onCareerChange,
  register,
  error,
  placeholder = 'Select a career...',
  showSearch = true,
  required = false,
}: CareerSelectorProps): JSX.Element {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isOpen, setIsOpen] = useState<boolean>(false);

  // Sort careers alphabetically by occupation name
  const sortedCareers = useMemo(() => {
    return [...careers].sort((a, b) =>
      a.occupation.name.localeCompare(b.occupation.name)
    );
  }, [careers]);

  const filteredCareers = useMemo(() => {
    let filtered = sortedCareers;
    
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = sortedCareers.filter((catalog) => {
        const occupation = catalog.occupation;
        return (
          occupation.name.toLowerCase().includes(query) ||
          occupation.soc_code.toLowerCase().includes(query) ||
          (occupation.description && occupation.description.toLowerCase().includes(query))
        );
      });
    }
    
    // Results are already sorted from sortedCareers
    return filtered;
  }, [sortedCareers, searchQuery]);

  const selectedCareer = useMemo(() => {
    return sortedCareers.find(
      (catalog) => catalog.occupation.career_id === selectedCareerId
    );
  }, [sortedCareers, selectedCareerId]);

  const handleSelectChange = (e: ChangeEvent<HTMLSelectElement>): void => {
    onCareerChange(e.target.value);
  };

  const handleSearchChange = (e: ChangeEvent<HTMLInputElement>): void => {
    setSearchQuery(e.target.value);
  };

  const handleOptionClick = (careerId: string): void => {
    onCareerChange(careerId);
    setIsOpen(false);
    setSearchQuery('');
  };

  return (
    <div className="career-selector-container">
      {showSearch ? (
        <div className="career-selector-dropdown">
          <div
            className={`career-selector-trigger ${error ? 'error' : ''}`}
            onClick={() => setIsOpen(!isOpen)}
          >
            {selectedCareer ? (
              <span className="career-selector-selected">
                {selectedCareer.occupation.name} ({selectedCareer.occupation.soc_code})
              </span>
            ) : (
              <span className="career-selector-placeholder">{placeholder}</span>
            )}
            <span className="career-selector-arrow">{isOpen ? '▲' : '▼'}</span>
          </div>
          {isOpen && (
            <div className="career-selector-menu">
              <div className="career-selector-search">
                <input
                  type="text"
                  className="career-selector-search-input"
                  placeholder="Search careers..."
                  value={searchQuery}
                  onChange={handleSearchChange}
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
              <div className="career-selector-options">
                {filteredCareers.length > 0 ? (
                  filteredCareers.map((catalog) => {
                    const occupation = catalog.occupation;
                    const isSelected = occupation.career_id === selectedCareerId;
                    return (
                      <div
                        key={occupation.career_id}
                        className={`career-selector-option ${isSelected ? 'selected' : ''}`}
                        onClick={() => handleOptionClick(occupation.career_id)}
                      >
                        <div className="career-option-name">{occupation.name}</div>
                        <div className="career-option-code">{occupation.soc_code}</div>
                        {occupation.description && (
                          <div className="career-option-description">
                            {occupation.description.substring(0, 100)}
                            {occupation.description.length > 100 ? '...' : ''}
                          </div>
                        )}
                      </div>
                    );
                  })
                ) : (
                  <div className="career-selector-no-results">
                    No careers found matching "{searchQuery}"
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ) : (
        <select
          className={`career-selector-select ${error ? 'error' : ''}`}
          value={selectedCareerId}
          onChange={handleSelectChange}
          {...register}
        >
          {!required && <option value="">{placeholder}</option>}
          {sortedCareers.map((catalog) => (
            <option
              key={catalog.occupation.career_id}
              value={catalog.occupation.career_id}
            >
              {catalog.occupation.name} ({catalog.occupation.soc_code})
            </option>
          ))}
        </select>
      )}
      {error && <span className="form-error">{error.message}</span>}
    </div>
  );
}

export default CareerSelector;

