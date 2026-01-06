import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

/**
 * Navigation Component
 * Provides navigation links to all major routes in the application
 */
function Navigation(): JSX.Element {
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState<boolean>(false);

  // Hide navigation on homepage
  if (location.pathname === '/') {
    return <></>;
  }

  const isActive = (path: string): boolean => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const toggleMenu = (): void => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = (): void => {
    setIsMenuOpen(false);
  };

  return (
    <nav className="navbar">
      <div className="nav-container">
        <button 
          className={`menu-toggle ${isMenuOpen ? 'active' : ''}`}
          onClick={toggleMenu}
          aria-label="Toggle menu"
        >
          <span className="menu-line"></span>
          <span className="menu-line"></span>
          <span className="menu-line"></span>
        </button>
        <div className={`nav-menu ${isMenuOpen ? 'open' : ''}`}>
          <Link 
            to="/" 
            className={`nav-link ${isActive('/') && location.pathname === '/' ? 'active' : ''}`}
            onClick={closeMenu}
          >
            Home
          </Link>
          <Link 
            to="/recommendations" 
            className={`nav-link ${isActive('/recommendations') ? 'active' : ''}`}
            onClick={closeMenu}
          >
            Recommendations
          </Link>
          <Link 
            to="/resume" 
            className={`nav-link ${isActive('/resume') ? 'active' : ''}`}
            onClick={closeMenu}
          >
            Resume
          </Link>
          <Link 
            to="/career-switch" 
            className={`nav-link ${isActive('/career-switch') ? 'active' : ''}`}
            onClick={closeMenu}
          >
            Career Switch
          </Link>
        </div>
      </div>
    </nav>
  );
}
export default Navigation;
