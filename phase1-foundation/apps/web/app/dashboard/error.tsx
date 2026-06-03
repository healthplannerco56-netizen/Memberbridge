"use client";
export default function DashboardError({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="px-8 py-7 flex items-center justify-center min-h-96">
      <div className="text-center max-w-sm">
        <p className="text-lg font-medium text-white mb-2">Something went wrong</p>
        <p className="text-sm text-zinc-500 mb-6">{error.message}</p>
        <button
          onClick={reset}
          className="px-4 py-2 bg-violet-600 hover:bg-violet-500 rounded-lg text-sm text-white font-medium transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
