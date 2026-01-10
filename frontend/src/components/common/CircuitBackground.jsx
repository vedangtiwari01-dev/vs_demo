const CircuitBackground = () => {
  return (
    <div className="absolute inset-0 pointer-events-none opacity-10">
      <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="circuit" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
            <line x1="0" y1="50" x2="100" y2="50" stroke="#00d4ff" strokeWidth="0.5"/>
            <line x1="50" y1="0" x2="50" y2="100" stroke="#00d4ff" strokeWidth="0.5"/>
            <circle cx="50" cy="50" r="2" fill="#00d4ff">
              <animate attributeName="opacity" values="0.3;1;0.3" dur="3s" repeatCount="indefinite"/>
            </circle>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#circuit)"/>
      </svg>
    </div>
  );
};

export default CircuitBackground;
