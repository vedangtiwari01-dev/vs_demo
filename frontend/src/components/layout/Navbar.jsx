import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Zap } from 'lucide-react';

const Navbar = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Analysis' },
    { path: '/stress-test', icon: Zap, label: 'Stress Testing' },
  ];

  return (
    <nav className="w-full bg-gradient-to-r from-secondary-900 via-secondary-800 to-secondary-900 shadow-2xl relative overflow-hidden">
      {/* Geometric Accents */}
      <div className="absolute top-0 left-1/4 w-64 h-full bg-primary-600/10 blur-3xl"></div>
      <div className="absolute top-0 right-0 w-24 h-24 bg-primary-500/20 rotate-45"></div>

      <div className="w-full px-6 relative z-10">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              {/* Wolf Logo */}
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-600 rounded-lg flex items-center justify-center shadow-lg relative overflow-hidden">
                {/* Simplified Wolf Face */}
                <svg viewBox="0 0 24 24" className="w-7 h-7 text-white" fill="currentColor">
                  {/* Wolf ears */}
                  <path d="M6 8 L8 4 L10 8 Z M14 8 L16 4 L18 8 Z" />
                  {/* Wolf head */}
                  <path d="M12 20 C8 20 5 17 5 13 C5 11 6 9 8 8 L10 8 C10 8 11 6 12 6 C13 6 14 8 14 8 L16 8 C18 9 19 11 19 13 C19 17 16 20 12 20 Z" />
                  {/* Wolf eyes */}
                  <circle cx="9" cy="12" r="1" fill="#0891b2" />
                  <circle cx="15" cy="12" r="1" fill="#0891b2" />
                  {/* Wolf nose */}
                  <path d="M12 14 L11 16 L12 16.5 L13 16 Z" />
                </svg>
              </div>
              <span className="ml-3 text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-blue-300 tracking-tight">
                ZenWolf
              </span>
            </div>
            <div className="hidden sm:ml-8 sm:flex sm:space-x-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`inline-flex items-center px-4 py-2 text-sm font-semibold rounded-lg transition-all ${
                      isActive
                        ? 'text-white bg-gradient-to-r from-primary-600 to-secondary-600 shadow-lg shadow-primary-500/30'
                        : 'text-cyan-200 hover:text-white hover:bg-secondary-700/50'
                    }`}
                  >
                    {Icon && <Icon className="h-4 w-4 mr-2" />}
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
