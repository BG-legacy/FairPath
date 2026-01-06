/**
 * RIASECInterestSelector Component
 * Selector for RIASEC interest categories with sliders
 */
import { UseFormRegisterReturn, FieldError, UseFormSetValue } from 'react-hook-form';
import { RIASEC_CATEGORIES } from '../../services/intake';
import './RIASECInterestSelector.css';

interface RIASECInterestSelectorProps {
  interests: Record<string, number>;
  onInterestsChange: (interests: Record<string, number>) => void;
  register?: UseFormRegisterReturn;
  setValue?: UseFormSetValue<any>;
  error?: FieldError;
  showLabels?: boolean;
}

export function RIASECInterestSelector({
  interests,
  onInterestsChange,
  register,
  setValue,
  error,
  showLabels = true,
}: RIASECInterestSelectorProps): JSX.Element {
  const handleInterestChange = (category: string, value: number): void => {
    const newInterests = { ...interests, [category]: value };
    onInterestsChange(newInterests);
    
    // Update form value if setValue is provided
    if (setValue) {
      setValue('interests', newInterests, { shouldValidate: true });
    }
  };

  return (
    <div className="riasec-selector-container">
      {showLabels && (
        <div className="riasec-header">
          <p className="riasec-description">
            Rate your interest in each category (0-7 scale)
          </p>
        </div>
      )}
      <div className="riasec-grid">
        {RIASEC_CATEGORIES.map((category) => {
          const value = interests[category] || 0;
          return (
            <div key={category} className="riasec-item">
              <label className="riasec-label">
                <span className="riasec-category">{category}</span>
                <div className="riasec-slider-wrapper">
                  <input
                    type="range"
                    className="riasec-slider"
                    min="0"
                    max="7"
                    step="0.1"
                    value={value}
                    onChange={(e) => handleInterestChange(category, Number(e.target.value))}
                    {...(register && { name: `interests.${category}` })}
                  />
                  <span className="riasec-value">{value.toFixed(1)}</span>
                </div>
              </label>
            </div>
          );
        })}
      </div>
      {error && <span className="form-error">{error.message}</span>}
    </div>
  );
}

export default RIASECInterestSelector;

