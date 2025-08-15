"use client";

import { LoginForm } from "./login-form";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/ui/card";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useToast } from "@workspace/ui/hooks/use-toast";
import { apiUrl } from "@/lib/constants";

export default function LoginPage() {
  const router = useRouter();
  const { toast } = useToast();

  /**
   * Handle login form submission.
   *
   * Sends credentials to the API, which should set HTTP-only cookies
   * for access and refresh tokens via the Set-Cookie header.
   * No tokens are stored in localStorage.
   */
  async function handleLogin(values: { email: string; password: string }) {
    const response = await fetch(`${apiUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(values),
      credentials: "include", // Ensure cookies are sent/received
    });

    if (!response.ok) {
      let error;
      try {
        error = await response.json();
      } catch {
        error = {};
      }
      throw new Error(error?.detail || "Login failed");
    }

    toast("Login successful!", {
      variant: "success",
    });
    router.push("/dashboard");
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Welcome back</CardTitle>
        <CardDescription>Sign in to your account to continue</CardDescription>
      </CardHeader>
      <CardContent>
        <LoginForm onSubmit={handleLogin} />
      </CardContent>
      <CardFooter className="flex flex-col space-y-2">
        <Link
          href="/forgot-password"
          className="text-sm text-muted-foreground hover:text-primary"
        >
          Forgot your password?
        </Link>
        <div className="text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link href="/signup" className="text-primary hover:underline">
            Sign up
          </Link>
        </div>
      </CardFooter>
    </Card>
  );
}
