import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Navigation } from "@/components/navigation";
import { AuthProvider } from "@/lib/auth-context";
import { ThemeProvider } from "@/lib/theme-context";
import { AnalyticsProvider } from "@/components/AnalyticsProvider";

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
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider>
          <AuthProvider>
            <AnalyticsProvider>
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900 overflow-x-hidden transition-colors">
              <Navigation />
              {/* Padding top for fixed nav */}
              <main className="container mx-auto px-4 py-8 pt-20 max-w-full overflow-x-hidden">
                {children}
              </main>
              <footer className="border-t border-gray-200 dark:border-gray-700 mt-12 py-6 text-center text-sm text-gray-600 dark:text-gray-400">
                <p>OpenThreat - Democratizing Threat Intelligence</p>
                <p className="mt-1">
                  Data sources: CISA KEV, NVD
                </p>
                <p className="mt-2">
                  <a
                    href="https://github.com/hoodinformatik/OpenThreat"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:underline"
                  >
                    GitHub
                  </a>
                  {" · "}
                  <a
                    href="mailto:hoodinformatik@gmail.com"
                    className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:underline"
                  >
                    Contact
                  </a>
                  {" · "}
                  <a
                    href="/privacy"
                    className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:underline"
                  >
                    Privacy Policy
                  </a>
                </p>
              </footer>
            </div>
            </AnalyticsProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
