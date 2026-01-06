import { useEffect, useRef, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './Home.css';

interface Particle {
  x: number;
  y: number;
  size: number;
  opacity: number;
  speed: number;
}

interface UseTypewriterOptions {
  text: string;
  speed?: number;
  delay?: number;
  onComplete?: () => void;
  enabled?: boolean;
}

const useTypewriter = ({ 
  text, 
  speed = 100, 
  delay = 0,
  onComplete,
  enabled = true
}: UseTypewriterOptions): string => {
  const [displayedText, setDisplayedText] = useState<string>('');
  const currentIndexRef = useRef<number>(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onCompleteRef = useRef(onComplete);
  const hasCompletedRef = useRef<boolean>(false);
  const hasStartedRef = useRef<boolean>(false);

  // Update ref when onComplete changes
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    // Reset when text changes or when first enabled
    if (!hasStartedRef.current || currentIndexRef.current === 0) {
      currentIndexRef.current = 0;
      setDisplayedText('');
      hasCompletedRef.current = false;
      hasStartedRef.current = true;
    }

    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }

    const startTyping = (): void => {
      const typeNextChar = (): void => {
        if (currentIndexRef.current < text.length) {
          setDisplayedText(text.slice(0, currentIndexRef.current + 1));
          currentIndexRef.current += 1;
          
          timeoutRef.current = setTimeout(typeNextChar, speed);
        } else if (!hasCompletedRef.current && onCompleteRef.current) {
          hasCompletedRef.current = true;
          onCompleteRef.current();
        }
      };

      typeNextChar();
    };

    if (delay > 0) {
      timeoutRef.current = setTimeout(startTyping, delay);
    } else {
      startTyping();
    }

    return (): void => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [text, speed, delay, enabled]);

  return displayedText;
};

function Home(): JSX.Element {
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [showTagline, setShowTagline] = useState<boolean>(false);

  const titleFullText = 'Fairpath';
  
  const handleTitleComplete = useCallback((): void => {
    setTimeout(() => {
      setShowTagline(true);
    }, 500);
  }, []);

  const titleText = useTypewriter({ 
    text: titleFullText,
    speed: 120,
    delay: 300,
    onComplete: handleTitleComplete
  });

  const isTitleComplete = titleText === titleFullText;

  const taglineFullText = 'Your Path to Career Success';
  
  const taglineText = useTypewriter({ 
    text: taglineFullText,
    speed: 70,
    delay: 0,
    enabled: showTagline
  });

  const isTaglineComplete = taglineText === taglineFullText;

  useEffect(() => {
    const canvas: HTMLCanvasElement | null = canvasRef.current;
    if (!canvas) return;

    const ctx: CanvasRenderingContext2D | null = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const resizeCanvas = (): void => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Create particles
    const particles: Particle[] = [];

    // Optimize particle count based on device
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

    // Animation loop
    const animate = (): void => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach((particle: Particle) => {
        // Update opacity for twinkling effect
        particle.opacity += Math.sin(Date.now() * 0.001 + particle.x) * 0.01;
        particle.opacity = Math.max(0.2, Math.min(1, particle.opacity));

        // Draw particle
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
    <div className="landing-page">
      <canvas ref={canvasRef} className="particles-canvas" />
      <div className="landing-content">
        <div className="title-container">
          <h1 className="landing-title">
            {titleText}
            {!isTitleComplete && <span className="cursor">|</span>}
          </h1>
          {showTagline && (
            <p className="tagline">
              {taglineText}
              {!isTaglineComplete && <span className="cursor">|</span>}
            </p>
          )}
        </div>
      </div>
      <div className="landing-footer">
        <button className="start-button" onClick={() => navigate('/recommendations')}>Start Here</button>
      </div>
    </div>
  );
}

export default Home;

