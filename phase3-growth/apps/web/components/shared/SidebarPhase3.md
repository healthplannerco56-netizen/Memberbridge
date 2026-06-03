# Sidebar — Phase 3 additions

Add to the NAV array in `apps/web/components/shared/Sidebar.tsx`
between "Event Log" and "Settings":

```ts
{ href: "/dashboard/dunning",   label: "Dunning",   icon: "✉" },
{ href: "/dashboard/analytics", label: "Analytics",  icon: "▲" },
```
