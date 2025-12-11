import React from 'react';
import clsx from 'clsx';

const Card = ({ children, className, title }) => {
  return (
    <div className={clsx('card', className)}>
      {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
      {children}
    </div>
  );
};

export default Card;
