import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "MemberBridge — Membership Billing Automation",
  description: "Automate community access based on subscription status.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en" className="dark">
        <body className={`${inter.variable} font-sans bg-zinc-950 text-zinc-100 antialiased`}>
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
