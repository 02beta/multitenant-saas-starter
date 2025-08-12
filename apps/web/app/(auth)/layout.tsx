export const metadata = {
  title: "Sign in | Multitenant SaaS Starter",
  description:
    "Securely sign in to your account to access your dashboard and projects.",
  openGraph: {
    title: "Sign in | Multitenant SaaS Starter",
    description:
      "Securely sign in to your account to access your dashboard and projects.",
    images: ["/images/og-images/og-image.png"],
  },
};

export default function AuthLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="min-h-svh w-full flex items-center justify-center p-6">
      <div className="w-full max-w-md">{children}</div>
    </div>
  );
}
