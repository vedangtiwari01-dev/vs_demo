const ModernLoading = ({ message = 'Loading...', subMessage = null, size = 'md' }) => {
  // Size configurations
  const sizeClasses = {
    sm: {
      container: 'min-h-[150px]',
      glow: 'w-20 h-20',
      outerRing: 'w-16 h-16 border-3',
      middleRing: 'w-12 h-12 border-3',
      innerRing: 'w-6 h-6 border-2',
      textMargin: 'mt-20',
      textSize: 'text-base',
      subTextSize: 'text-xs'
    },
    md: {
      container: 'min-h-[200px]',
      glow: 'w-32 h-32',
      outerRing: 'w-24 h-24 border-4',
      middleRing: 'w-16 h-16 border-4',
      innerRing: 'w-8 h-8 border-2',
      textMargin: 'mt-32',
      textSize: 'text-lg',
      subTextSize: 'text-sm'
    },
    lg: {
      container: 'min-h-[250px]',
      glow: 'w-40 h-40',
      outerRing: 'w-32 h-32 border-4',
      middleRing: 'w-20 h-20 border-4',
      innerRing: 'w-10 h-10 border-3',
      textMargin: 'mt-40',
      textSize: 'text-xl',
      subTextSize: 'text-base'
    }
  };

  const config = sizeClasses[size] || sizeClasses.md;

  return (
    <div className={`flex items-center justify-center ${config.container} relative`}>
      {/* Pulsing glow background */}
      <div className="absolute animate-pulse-slow">
        <div className={`${config.glow} bg-gradient-to-br from-primary-500/20 to-secondary-500/20 rounded-full blur-2xl`} />
      </div>

      {/* Triple ring spinner system */}
      <div className="relative z-10">
        {/* Outer ring - slow rotation (3s) */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className={`${config.outerRing} border-primary-200 border-t-primary-600 rounded-full animate-spin-slow`} />
        </div>

        {/* Middle ring - reverse rotation (2s) */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className={`${config.middleRing} border-secondary-200 border-t-secondary-600 rounded-full animate-spin-reverse`} />
        </div>

        {/* Inner ring - fast rotation (1s) */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className={`${config.innerRing} border-primary-400 border-t-transparent rounded-full animate-spin`} />
        </div>
      </div>

      {/* Text with gradient */}
      <div className={`absolute ${config.textMargin} text-center max-w-md px-4`}>
        <p className={`${config.textSize} font-semibold text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-secondary-600`}>
          {message}
        </p>
        {subMessage && (
          <p className={`${config.subTextSize} text-secondary-600 mt-2`}>
            {subMessage}
          </p>
        )}
      </div>
    </div>
  );
};

export default ModernLoading;
