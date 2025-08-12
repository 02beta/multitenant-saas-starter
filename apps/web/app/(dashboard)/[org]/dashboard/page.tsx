import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard | Multitenant SaaS Starter",
  description: "Your organization dashboard.",
};

interface DashboardPageProps {
  params: {
    org: string;
  };
}

export default function DashboardPage(props: DashboardPageProps) {
  const { params } = props;

  // In a real app, fetch profile using token
  const user = {
    full_name: "Ada Lovelace",
    avatar_url: "/images/logos/logo-light.png",
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
        <p className="text-muted-foreground">Organization: {params.org}</p>
      </div>
    </div>
  );
}
