"use client";

import { SignupForm } from "@workspace/ui/components/auth/signup-form";
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

export default function SignupPage() {
  const { toast } = useToast();
  const router = useRouter();

  async function handleSignup(values: {
    firstName: string;
    lastName: string;
    organizationName?: string;
    email: string;
    password: string;
  }) {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/auth/signup`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: values.firstName,
          last_name: values.lastName,
          organization_name: values.organizationName,
          email: values.email,
          password: values.password,
        }),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Signup failed");
    }

    toast(
      "Signup successful! Please check your email for a verification link.",
      {
        variant: "success",
      }
    );
    router.push("/login");
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create an account</CardTitle>
        <CardDescription>Get started with your free account</CardDescription>
      </CardHeader>
      <CardContent>
        <SignupForm onSubmit={handleSignup} />
      </CardContent>
      <CardFooter>
        <div className="text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </div>
      </CardFooter>
    </Card>
  );
}
