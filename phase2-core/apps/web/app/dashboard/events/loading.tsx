export default function Loading() {
  return (
    <div className="px-8 py-7 space-y-6 animate-pulse">
      <div className="h-6 w-40 bg-zinc-800 rounded" />
      <div className="bg-zinc-900/60 border border-white/6 rounded-xl h-96" />
    </div>
  );
}
