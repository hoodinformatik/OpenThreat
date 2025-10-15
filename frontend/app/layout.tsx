import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Navigation } from "@/components/navigation";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "OpenThreat - Public Threat Intelligence Dashboard",
  description: "Democratizing Threat Intelligence - Free and open-source CVE tracking",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          <Navigation />
          <main className="container mx-auto px-4 py-8">
            {children}
          </main>
          <footer className="border-t mt-12 py-6 text-center text-sm text-gray-600">
            <p>OpenThreat - Democratizing Threat Intelligence</p>
            <p className="mt-1">
              Data sources: CISA KEV, NVD, CVE Search, MITRE ATT&CK
            </p>
          </footer>
        </div>
      </body>
    </html>
  );
}
