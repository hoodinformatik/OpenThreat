import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Navigation } from "@/components/navigation";
import { AuthProvider } from "@/lib/auth-context";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "OpenThreat - Public Threat Intelligence Dashboard",
  description: "Democratizing Threat Intelligence - Free and open-source CVE tracking",
  icons: {
    icon: [
      { url: '/favicon.svg', type: 'image/svg+xml' },
    ],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <div className="min-h-screen bg-gray-50 overflow-x-hidden">
            <Navigation />
            {/* Padding top for fixed nav */}
            <main className="container mx-auto px-4 py-8 pt-20 max-w-full overflow-x-hidden">
              {children}
            </main>
            <footer className="border-t mt-12 py-6 text-center text-sm text-gray-600">
              <p>OpenThreat - Democratizing Threat Intelligence</p>
              <p className="mt-1">
                Data sources: CISA KEV, NVD, BSI CERT-Bund
              </p>
              <p className="mt-2">
                <a
                  href="https://github.com/hoodinformatik/OpenThreat"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-700 hover:underline"
                >
                  GitHub
                </a>
                {" · "}
                <a
                  href="mailto:hoodinformatik@gmail.com"
                  className="text-blue-600 hover:text-blue-700 hover:underline"
                >
                  Contact
                </a>
                {" · "}
                <a
                  href="/privacy"
                  className="text-blue-600 hover:text-blue-700 hover:underline"
                >
                  Privacy Policy
                </a>
              </p>
            </footer>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
