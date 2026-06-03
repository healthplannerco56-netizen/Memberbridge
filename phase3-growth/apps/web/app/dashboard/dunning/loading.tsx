export default function Loading() {
  return (
    <div className="px-8 py-7 space-y-6 animate-pulse">
      <div className="h-6 w-40 bg-zinc-800 rounded" />
      <div className="grid grid-cols-3 gap-4">
        {[...Array(3)].map((_,i)=><div key={i} className="bg-zinc-900/60 border border-white/6 rounded-xl h-28"/>)}
      </div>
      <div className="grid grid-cols-2 gap-5">
        <div className="bg-zinc-900/60 border border-white/6 rounded-xl h-64"/>
        <div className="bg-zinc-900/60 border border-white/6 rounded-xl h-64"/>
      </div>
    </div>
  );
}
