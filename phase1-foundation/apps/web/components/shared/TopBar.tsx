import { UserButton } from "@clerk/nextjs";

export function TopBar() {
  return (
    <div className="h-12 border-b border-white/5 flex items-center justify-between px-8 bg-zinc-950/80 backdrop-blur-sm flex-shrink-0">
      <div />
      <UserButton afterSignOutUrl="/sign-in" />
    </div>
  );
}
