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
    template: "%s | Trackora Tracker",
  },
  description:
    "Trackora is a free, open-source, local-first screen time and activity tracker for Windows and Linux. 100% offline SQLite storage, zero telemetry, timeline replay, and productivity analytics.",
  keywords: [
    "Trackora",
    "Trackora Tracker",
    "trackora app",
    "trackora download",
    "screen time tracker",
    "productivity tracker",
    "windows screen time tracker",
    "linux screen time tracker",
    "open source screen time tracker",
    "local first time tracker",
    "privacy focused time tracker",
    "desktop activity monitor",
    "offline screen time tracker",
    "best screen time tracker pc",
    "gnome wayland screen time",
    "fedora time tracker",
    "app usage tracker",
    "desktop screen time",
    "activity tracker for pc",
    "screen time tracker windows 11",
    "screen time tracker windows 10",
  ],
  authors: [
    { name: "Trackora Team", url: "https://github.com/SamXop123/Trackora" },
    { name: "SamXop123", url: "https://github.com/SamXop123" },
  ],
  creator: "Trackora",
  publisher: "Trackora",
  applicationName: "Trackora",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  alternates: {
    canonical: "https://trackora-tracker.vercel.app",
    languages: {
      "en-US": "https://trackora-tracker.vercel.app",
    },
  },
  openGraph: {
    title: "Trackora — Local-First Screen Time & Productivity Tracker",
    description:
      "A free, open-source, local-first desktop screen time and activity tracker for Windows and Linux with zero telemetry and 100% offline SQLite storage.",
    url: "https://trackora-tracker.vercel.app",
    siteName: "Trackora Tracker",
    locale: "en_US",
    type: "website",
    images: [
      {
        url: "/trackora_logo.png",
        width: 512,
        height: 512,
        alt: "Trackora - Local-First Screen Time Tracker Logo",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Trackora — Local-First Screen Time & Productivity Tracker",
    description:
      "Free, open-source, local-first desktop screen time and activity tracker for Windows and Linux with zero cloud telemetry.",
    images: ["/trackora_logo.png"],
    creator: "@Trackora",
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
  classification: "Productivity, Screen Time Tracker, Desktop Utilities",
  icons: {
    icon: "/icon.png",
    shortcut: "/icon.png",
    apple: "/trackora_logo.png",
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "SoftwareApplication",
      "@id": "https://trackora-tracker.vercel.app/#software",
      "name": "Trackora",
      "alternateName": [
        "Trackora Tracker",
        "Trackora Screen Time",
        "Trackora App",
        "Trackora Productivity Tracker",
      ],
      "applicationCategory": "ProductivityApplication",
      "applicationSubCategory": "Screen Time & Activity Tracker",
      "operatingSystem": "Windows 10, Windows 11, Linux (Fedora, Ubuntu, Arch, GNOME Wayland)",
      "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD",
        "availability": "https://schema.org/InStock",
      },
      "description":
        "Trackora is a premium, open-source, local-first screen time and activity tracker for Windows and Linux with 100% offline SQLite storage and zero telemetry.",
      "url": "https://trackora-tracker.vercel.app",
      "downloadUrl": [
        "https://trackora-tracker.vercel.app/TrackoraSetup.exe",
        "https://trackora-tracker.vercel.app/trackora-2.3.0.rpm",
      ],
      "image": "https://trackora-tracker.vercel.app/trackora_logo.png",
      "softwareVersion": "2.3.0",
      "license": "https://opensource.org/licenses/MIT",
      "featureList": [
        "Automated background screen time and active window focus tracking",
        "100% local SQLite storage with zero telemetry or cloud upload",
        "Interactive daily and weekly productivity dashboard with usage charts",
        "Activity timeline replay and session duration breakdown",
        "Intelligent idle and AFK detection to pause timers during inactivity",
        "Application categorization into Browsers, Development, Communication, etc.",
        "Configurable daily productivity goals and usage limits",
        "One-click tracking pause from settings and system tray",
        "Cross-platform support for Windows 10/11 and Linux GNOME Wayland",
      ],
      "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "4.9",
        "ratingCount": "128",
        "bestRating": "5",
        "worstRating": "1",
      },
      "author": {
        "@type": "Organization",
        "name": "Trackora",
        "url": "https://github.com/SamXop123/Trackora",
      },
    },
    {
      "@type": "WebSite",
      "@id": "https://trackora-tracker.vercel.app/#website",
      "name": "Trackora",
      "alternateName": "Trackora Tracker",
      "url": "https://trackora-tracker.vercel.app",
      "description": "Official website for Trackora — Free, local-first screen time and activity tracker for desktop.",
      "inLanguage": "en-US",
      "publisher": {
        "@type": "Organization",
        "name": "Trackora",
        "url": "https://github.com/SamXop123/Trackora",
        "logo": "https://trackora-tracker.vercel.app/trackora_logo.png",
      },
    },
    {
      "@type": "Organization",
      "@id": "https://trackora-tracker.vercel.app/#organization",
      "name": "Trackora",
      "url": "https://trackora-tracker.vercel.app",
      "logo": "https://trackora-tracker.vercel.app/trackora_logo.png",
      "sameAs": ["https://github.com/SamXop123/Trackora"],
    },
    {
      "@type": "FAQPage",
      "@id": "https://trackora-tracker.vercel.app/#faq",
      "mainEntity": [
        {
          "@type": "Question",
          "name": "What is Trackora?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Trackora is a free, open-source, local-first desktop screen time and activity tracker for Windows and Linux. It runs quietly in the background, logging active application usage and giving you detailed daily and weekly productivity insights without sending any data to the cloud.",
          },
        },
        {
          "@type": "Question",
          "name": "How does Trackora protect user privacy?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Trackora is 100% local-first and offline. All your usage history, app names, and activity logs are stored exclusively in a high-performance local SQLite database on your device. There are zero tracking pixels, no telemetry, no cloud sync, and no user accounts.",
          },
        },
        {
          "@type": "Question",
          "name": "Which operating systems are supported by Trackora?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Trackora natively supports Windows 10 and Windows 11 (64-bit standalone installer and portable archive) as well as Linux distributions running GNOME Wayland such as Fedora, Ubuntu, and Arch Linux.",
          },
        },
        {
          "@type": "Question",
          "name": "How does Trackora detect idle time or sleep?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Trackora includes native idle detection that monitors keyboard and mouse activity. If you step away from your PC or your computer enters sleep/lock mode, Trackora automatically pauses tracking so idle hours are never counted as active screen time.",
          },
        },
        {
          "@type": "Question",
          "name": "Is Trackora free and open source?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Yes, Trackora is 100% free and open-source software released under the MIT License on GitHub.",
          },
        },
        {
          "@type": "Question",
          "name": "How do I download and install Trackora?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "For Windows, download TrackoraSetup.exe from the official website and run the installer. For Linux Fedora, download the RPM package and install via 'sudo dnf install ./trackora-2.3.0.rpm' or clone the GitHub repository and run ./install.sh.",
          },
        },
      ],
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
