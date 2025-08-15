"use server";

import { getCurrentUser, getUserMemberships } from "@/lib/auth.server";
import { redirect } from "next/navigation";

interface Membership {
  id: string;
  organization_name: string;
  organization_id: string;
  is_active: boolean;
  role_id: number;
  role_name: string;
}

export default async function DashboardPage() {
  const user = await getCurrentUser();

  if (!user) {
    redirect("/login");
  }

  const memberships = await getUserMemberships();

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-4">Dashboard</h1>
      <div className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold">
            Welcome, {user.user.full_name}!
          </h2>
          <p className="text-muted-foreground">{user.user.email}</p>
        </div>

        {user.organization && (
          <div>
            <h3 className="font-semibold">Current Organization</h3>
            <p>{user.organization.name}</p>
          </div>
        )}

        <div>
          <h3 className="font-semibold">Your Organizations</h3>
          <ul className="list-disc pl-5">
            {memberships.map((membership: Membership) => (
              <li key={membership.id}>
                {membership.organization_name} &ndash; {membership.role_name}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
