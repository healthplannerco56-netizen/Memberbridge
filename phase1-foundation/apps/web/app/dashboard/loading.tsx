export default function DashboardLoading() {
  return (
    <div className="px-8 py-7 space-y-7 animate-pulse">
      <div>
        <div className="h-6 w-32 bg-zinc-800 rounded" />
        <div className="h-4 w-48 bg-zinc-800 rounded mt-2" />
      </div>
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-zinc-900/60 border border-white/6 rounded-xl p-5 h-28" />
        ))}
      </div>
      <div className="bg-zinc-900/60 border border-white/6 rounded-xl h-64" />
    </div>
  );
}
