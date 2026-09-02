import type { Metadata } from "next";
import { Outfit, JetBrains_Mono } from "next/font/google";
import "./globals.css";

import { Analytics } from "@vercel/analytics/react";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://trackora-tracker.vercel.app"),
  title: {
    default: "Trackora — Local-First Screen Time & Productivity Tracker",
    template: "%s | Trackora",
  },
  description:
    "Trackora is a premium, privacy-focused, local-first desktop screen time and activity tracker for Windows and Linux. 100% offline SQLite storage with zero telemetry.",
  keywords: [
    "screen time tracker",
    "productivity tracker",
    "activity tracker",
    "local first app",
    "privacy focused time tracker",
    "windows screen time",
    "linux time tracker",
    "desktop activity analytics",
    "open source screen time tracker",
    "Trackora",
  ],
  authors: [{ name: "Trackora Team", url: "https://github.com/SamXop123/Trackora" }],
  creator: "Trackora",
  publisher: "Trackora",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  alternates: {
    canonical: "https://trackora-tracker.vercel.app",
  },
  openGraph: {
    title: "Trackora — Local-First Screen Time & Productivity Tracker",
    description:
      "A premium, local-first, privacy-focused screen time and activity tracker for Windows and Linux with zero telemetry.",
    url: "https://trackora-tracker.vercel.app",
    siteName: "Trackora",
    locale: "en_US",
    type: "website",
    images: [
      {
        url: "/trackora_logo.png",
        width: 512,
        height: 512,
        alt: "Trackora Logo",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Trackora — Local-First Screen Time & Productivity Tracker",
    description:
      "A premium, local-first, privacy-focused screen time and activity tracker for Windows and Linux.",
    images: ["/trackora_logo.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  verification: {
    google: "google2b4b3deddceb3809",
  },
  category: "technology",
};

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "SoftwareApplication",
      "name": "Trackora",
      "applicationCategory": "ProductivityApplication",
      "operatingSystem": "Windows 10, Windows 11, Linux GNOME Wayland",
      "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD",
      },
      "description":
        "A premium, local-first, privacy-focused desktop screen time and productivity tracker.",
      "url": "https://trackora-tracker.vercel.app",
      "downloadUrl": "https://trackora-tracker.vercel.app/TrackoraSetup.exe",
      "image": "https://trackora-tracker.vercel.app/trackora_logo.png",
      "softwareVersion": "2.2.1",
      "author": {
        "@type": "Organization",
        "name": "Trackora",
        "url": "https://github.com/SamXop123/Trackora",
      },
    },
    {
      "@type": "WebSite",
      "name": "Trackora",
      "url": "https://trackora-tracker.vercel.app",
      "description": "Local-first screen time and activity analytics desktop suite.",
      "inLanguage": "en-US",
    },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${outfit.variable} ${jetbrainsMono.variable}`}>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
