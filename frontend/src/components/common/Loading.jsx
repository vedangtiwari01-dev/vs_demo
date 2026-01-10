import ModernLoading from './ModernLoading';

const Loading = ({ message = 'Loading...' }) => {
  return (
    <div className="flex items-center justify-center p-8">
      <ModernLoading message={message} size="sm" />
    </div>
  );
};

export default Loading;
