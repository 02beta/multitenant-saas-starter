"use server";

import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth.server";

export default async function HomePage() {
  const user = await getCurrentUser();
  console.log(user);
  if (user) {
    redirect("/dashboard");
  } else {
    redirect("/login");
  }
}
