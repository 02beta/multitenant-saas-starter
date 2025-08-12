import { getSubdomainData } from "@/lib/subdomains";
import { Metadata } from "next";
import { log, useLogger } from "next-axiom";

export const metadata: Metadata = {
  title: "Dashboard | Multitenant SaaS Starter",
  description: "Your organization dashboard.",
};

type DashboardPageProps = {
  params: {
    org: string;
  };
};

export default async function DashboardPage({
  params,
}: {
  params: Promise<{ org: string }>;
}): Promise<React.ReactElement> {
  const log = useLogger({ source: "dashboard.tsx" });
  const { org } = await params;
  const subdomainData = await getSubdomainData(org);

  if (!subdomainData) {
    log.error("Organization not found", { org });
    return <div>Organization not found</div>;
  }

  // In a real app, fetch profile using token
  const user = {
    full_name: "Ada Lovelace",
    avatar_url:
      "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=facearea&w=256&h=256&facepad=2",
  };

  return (
    <div className="min-h-svh w-full flex items-center justify-center p-6">
      <div className="text-center space-y-2">
        <img
          src={user.avatar_url}
          alt="Avatar"
          className="mx-auto size-16 rounded-full"
        />
        <h1 className="text-2xl font-bold">Hello {user.full_name}</h1>
        <p className="text-muted-foreground">Organization: {org}</p>
      </div>
    </div>
  );
}
