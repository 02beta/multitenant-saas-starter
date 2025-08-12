import localFont from "next/font/local";
import { ThemeProvider } from "@workspace/ui/components/theme-provider";

import { Providers } from "@/components/providers";
import { Toaster } from "@workspace/ui/components/ui/sonner";
import { AxiomWebVitals } from "next-axiom";

import "@workspace/ui/globals.css";

const fontMono = localFont({
  src: "../public/fonts/aeonikmonovf.woff2",
  variable: "--font-mono",
});

const fontSans = localFont({
  src: "../public/fonts/aeonikfonovf.woff2",
  variable: "--font-sans",
  display: "swap",
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${fontSans.variable} ${fontMono.variable} font-sans antialiased `}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <Providers>{children}</Providers>
          <Toaster />
          <AxiomWebVitals />
        </ThemeProvider>
      </body>
    </html>
  );
}
