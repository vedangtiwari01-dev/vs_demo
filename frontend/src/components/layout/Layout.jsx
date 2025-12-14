import React from 'react';
import Navbar from './Navbar';
import { Toaster } from 'react-hot-toast';

const Layout = ({ children }) => {
  return (
    <div className="w-full min-h-screen bg-gray-50">
      <Navbar />
      <main className="w-full">
        {children}
      </main>
      <Toaster position="top-right" />
    </div>
  );
};

export default Layout;
