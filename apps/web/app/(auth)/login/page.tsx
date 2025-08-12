"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { log } from "next-axiom";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/ui/card";
import { Button } from "@workspace/ui/components/ui/button";
import { Input } from "@workspace/ui/components/ui/input";
import { Label } from "@workspace/ui/components/ui/label";
import { useToast } from "@workspace/ui/hooks";

export default function LoginPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    log.debug("login page loaded", {
      page: "login",
      timestamp: new Date().toISOString(),
    });
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    log.info("login attempt", {
      email: email,
      timestamp: new Date().toISOString(),
    });

    try {
      const res = await fetch(
        process.env.NEXT_PUBLIC_API_URL + "/v1/auth/login",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        }
      );
      if (!res.ok) throw new Error("Invalid credentials");
      const data = await res.json();

      log.info("login successful", {
        email: email,
        organization_slug: data.organization_slug,
        timestamp: new Date().toISOString(),
      });

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token ?? "");

      const slug = data.organization_slug;
      if (slug) {
        router.replace(`/${slug}/dashboard`);
      } else {
        router.replace(`/dashboard`);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        toast(err.message, { variant: "error" });
        log.error("login failed", {
          email: email,
          error: err.message,
          timestamp: new Date().toISOString(),
        });
      } else {
        toast("An unknown error occurred", { variant: "error" });
        log.error("login failed", {
          email: email,
          error: "An unknown error occurred",
          timestamp: new Date().toISOString(),
        });
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Sign in</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Signing in..." : "Sign in"}
          </Button>
          <div className="flex items-center justify-between text-sm">
            <Link href="/signup" className="underline">
              Create an account
            </Link>
            <Link href="/forgot-password" className="underline">
              Forgot password?
            </Link>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
