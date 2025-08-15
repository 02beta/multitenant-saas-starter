"use client";

import { Suspense } from "react";
import { ResetPasswordForm } from "./reset-password-form";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/ui/card";
import { useRouter, useSearchParams } from "next/navigation";
import { useToast } from "@workspace/ui/hooks/use-toast";

/**
 * Note:
 * We are NOT getting the value of the token from an HTTP-only cookie.
 * The token is being read from the URL query string (?token=...).
 * HTTP-only cookies cannot be accessed from client-side JavaScript.
 * If the backend sets the reset token as an HTTP-only cookie, it would
 * not be accessible here. This code expects the token to be present
 * in the URL as a query parameter.
 */

function ResetPasswordPageContent() {
  const { toast } = useToast();
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  async function handleResetPassword(values: { password: string }) {
    if (!token) {
      toast("Invalid reset link", {
        variant: "error",
      });
      return;
    }

    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/auth/reset-password`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token,
          password: values.password,
        }),
        // credentials: "include" // Not needed for token in body/query
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to reset password");
    }

    toast("Password reset successful! Please login with your new password.", {
      variant: "success",
    });
    router.push("/login");
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Reset your password</CardTitle>
        <CardDescription>Enter your new password below</CardDescription>
      </CardHeader>
      <CardContent>
        <ResetPasswordForm onSubmit={handleResetPassword} />
      </CardContent>
    </Card>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordPageContent />
    </Suspense>
  );
}
