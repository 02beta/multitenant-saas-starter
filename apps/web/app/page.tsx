import { Button } from "@workspace/ui/components/ui/button";
import { AxiomDemo } from "@/components/axiom-demo";
import Link from "next/link";

export default function Page() {
  return (
    <div className="flex items-center justify-center min-h-svh">
      <div className="flex flex-col items-center justify-center gap-4">
        <h1 className="text-2xl font-bold">Hello World</h1>
        <Button size="sm" asChild>
          <Link href="/login">Go to login</Link>
        </Button>
        <AxiomDemo />
      </div>
    </div>
  );
}
