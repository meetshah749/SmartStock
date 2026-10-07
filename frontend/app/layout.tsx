import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { AuthProvider } from "@/lib/auth";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { StockAssistant } from "@/components/StockAssistant";

export const metadata: Metadata = {
  title: "SmartStock AI — Financial Intelligence & Virtual Trading Platform",
  description: "Production-oriented financial market intelligence, explainable AI analytics, historical backtesting, and virtual trading platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen flex flex-col font-sans antialiased selection:bg-brand-primary selection:text-white">
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            <Header />
            <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
              {children}
            </main>
            <Footer />
            <StockAssistant />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
