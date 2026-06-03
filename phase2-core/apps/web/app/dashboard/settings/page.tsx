import { api } from "@/lib/api";
import { SettingsClient } from "./SettingsClient";

export default async function SettingsPage() {
  const [billing, community] = await Promise.all([
    api.listBilling(),
    api.listCommunity(),
  ]);
  return <SettingsClient billing={billing as any[]} community={community as any[]} />;
}
