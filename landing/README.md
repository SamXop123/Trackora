# Trackora Landing Page Experience

This directory houses the web experience for **Trackora**—a local-first, privacy-focused activity and screen time tracker. 

Unlike traditional SaaS marketing pages, the website is structured as an interactive, immersive **Desktop Client Simulator** mimicking a premium desktop application framework.

---

## 🚀 Getting Started

To run the development server locally:

```bash
# 1. Navigate to the landing directory (if not already there)
cd landing

# 2. Install dependencies
npm install

# 3. Start the dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to experience the simulator.

---

## 🛠️ Build & Static Exports

The website compiles to optimized, static HTML/JS pages to guarantee zero-latency load times:

```bash
# Compile and output production build
npm run build
```

The output is bundled under the `.next/` cache folder and is fully optimized for static web hosting.

---

## 📁 Architecture & Components

The interface utilizes Next.js App Router, Framer Motion, and HSL custom color tokens:

```
landing/
├── src/
│   ├── app/
│   │   ├── globals.css         # Styling system, theme HSL variables, animations
│   │   ├── layout.tsx          # Font loads (Outfit & JetBrains Mono)
│   │   ├── page.tsx            # View coordinator & scroll-wheel listeners
│   │   └── icon.png            # Web favicon (Trackora official logo)
│   └── components/
│       ├── Starfield.tsx       # Canvas backdrop with warp speed props
│       ├── AppFrame.tsx        # Desktop client window layout wrapper
│       ├── Sidebar.tsx         # Sidebar navigator with direct download link CTAs
│       ├── CommandPalette.tsx  # Keyboard shortcut command menu (Ctrl + K)
│       └── views/
│           ├── IntroView.tsx   # Intro landing: "where did today go? trackora knows."
│           ├── ReplayView.tsx  # Immersive chronological workday timeline with conclusion
│           ├── DashboardView.tsx # Interactive dashboard tracking Minecraft, Spotify, and more
│           ├── PipelineView.tsx # Isometric data layers with developer specs toggles
│           ├── PrivacyView.tsx # Offline database cylinder and crash recovery test simulator
│           └── DownloadView.tsx # Install commands and direct RPM package downloads
```

---

## 🎨 Creative Highlights

*   **Continuous Narrative**: Navigation is driven by a debounced scroll listener (`page.tsx`) that transitions the visitor smoothly between scenes.
*   **Replay Conclusion**: After stepping through the workday timeline, the interface transitions into a slow-fading conclusion sequence highlighting the core value proposition: *"Today is already fading into a vague memory... Trackora remembers."*
*   **Interactive Toggles**: Inside **Inside Trackora** (`PipelineView.tsx`), low-level technical specifics are hidden behind a **For Developers** toggle to preserve a clean, human-benefit narrative for everyday users.
*   **Website Icon & Official Logo**: The official `trackora_logo.png` is integrated next to branding titles and used as the site's favicon.
