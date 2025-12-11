'use client';

import React, { useState } from 'react';
import { motion, Variants } from 'framer-motion';
import { 
  Apple, 
  Monitor, 
  Terminal, 
  Download, 
  ChevronRight, 
  ShieldCheck, 
  AlertCircle 
} from 'lucide-react';
import Link from 'next/link';

type ReleaseStatus = 'stable' | 'beta' | 'coming-soon';

interface Platform {
  id: string;
  name: string;
  icon: React.ElementType;
  description: string;
  version: string;
  status: ReleaseStatus;
  primaryAction?: {
    label: string;
    subLabel?: string;
  };
  architectures?: string[];
}

const platforms: Platform[] = [
  {
    id: 'macos',
    name: 'macOS',
    icon: Apple,
    description: 'Requires macOS 14.0 (Sonoma) or later.',
    version: 'v1.0.0-beta',
    status: 'coming-soon', 
    architectures: ['Apple Silicon', 'Intel'],
    primaryAction: {
      label: 'Join Waitlist', 
    }
  },
  {
    id: 'windows',
    name: 'Windows',
    icon: Monitor,
    description: 'Windows 10/11 w/ WSL2 support recommended.',
    version: 'v1.0.0-beta',
    status: 'coming-soon',
    primaryAction: {
      label: 'Join Waitlist',
    }
  },
  {
    id: 'linux',
    name: 'Linux',
    icon: Terminal,
    description: 'Debian/Ubuntu based distributions.',
    version: 'v1.0.0-beta',
    status: 'coming-soon', 
    architectures: ['x86_64', 'ARM64'],
    primaryAction: {
      label: 'Join Waitlist', 
    }
  }
];

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.4, ease: "easeOut" }
  }
};

export default function DownloadPage() {
  const [selectedArch, setSelectedArch] = useState<Record<string, string>>({
    macos: 'Apple Silicon',
    linux: 'x86_64'
  });

  return (
    <main className="min-h-screen pt-32 pb-20 px-6 bg-[#FAFAFA] dark:bg-[#0A0A0A] text-neutral-900 dark:text-neutral-50 font-sans selection:bg-[#F08787] selection:text-white">
      
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-5xl mx-auto mb-16 text-center"
      >
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">
          Install Engram
        </h1>
        <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto">
          Local-first, private-by-design. Choose your environment to begin. 
          <br className="hidden md:block" />
          Currently in <span className="text-[#F08787] font-medium">Public Beta</span>.
        </p>
      </motion.div>

      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6"
      >
        {platforms.map((platform) => (
          <PlatformCard 
            key={platform.id} 
            platform={platform} 
            selectedArch={selectedArch[platform.id]}
            onArchSelect={(arch) => setSelectedArch(prev => ({ ...prev, [platform.id]: arch }))}
          />
        ))}
      </motion.div>

      <motion.div 
        variants={itemVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="max-w-2xl mx-auto mt-24 text-center border-t border-neutral-200 dark:border-neutral-800 pt-12"
      >
        <div className="flex items-center justify-center gap-2 mb-4 text-neutral-900 dark:text-white font-medium">
          <ShieldCheck className="w-5 h-5 text-[#F08787]" />
          <span>Verify your download</span>
        </div>
        <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-6">
          Security is non-negotiable. Always verify the SHA-256 checksum of your binary before installation to ensure integrity.
        </p>
        <div className="flex items-center justify-center gap-4 text-sm">
          <Link href="#" className="hover:text-[#F08787] transition-colors underline decoration-neutral-300 dark:decoration-neutral-700 underline-offset-4">
            View Checksums
          </Link>
          <span className="text-neutral-300 dark:text-neutral-700">|</span>
          <Link href="#" className="hover:text-[#F08787] transition-colors underline decoration-neutral-300 dark:decoration-neutral-700 underline-offset-4">
            PGP Signatures
          </Link>
        </div>
      </motion.div>

    </main>
  );
}

function PlatformCard({ 
  platform, 
  selectedArch, 
  onArchSelect 
}: { 
  platform: Platform; 
  selectedArch?: string;
  onArchSelect: (arch: string) => void;
}) {
  const isDownloadable = platform.status !== 'coming-soon';
  const Icon = platform.icon;

  return (
    <motion.div 
      variants={itemVariants}
      className={`
        relative flex flex-col p-8 rounded-2xl border
        transition-all duration-300 group
        bg-white dark:bg-[#111] border-neutral-200 dark:border-neutral-800 
        hover:border-[#F08787]/50 dark:hover:border-[#F08787]/50
      `}
    >
      <div className="absolute top-6 right-6">
        <span className="text-xs font-mono px-2 py-1 rounded-full border bg-neutral-100 dark:bg-neutral-800 text-neutral-500 border-neutral-200 dark:border-neutral-700">
          {platform.status === 'coming-soon' ? 'Upcoming' : platform.version}
        </span>
      </div>

      <div className="mb-6">
        <div className="w-12 h-12 bg-neutral-100 dark:bg-neutral-900 rounded-xl flex items-center justify-center mb-4 text-neutral-900 dark:text-white">
          <Icon className="w-6 h-6" strokeWidth={1.5} />
        </div>
        <h3 className="text-xl font-bold">{platform.name}</h3>
        <p className="text-sm text-neutral-500 mt-2 h-10">
          {platform.description}
        </p>
      </div>

      {isDownloadable && platform.architectures && (
        <div className="flex bg-neutral-100 dark:bg-neutral-900/50 p-1 rounded-lg mb-6 w-fit">
          {platform.architectures.map((arch) => (
            <button
              key={arch}
              onClick={() => onArchSelect(arch)}
              className={`
                px-3 py-1 text-xs font-medium rounded-md transition-all
                ${selectedArch === arch 
                  ? 'bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white shadow-sm' 
                  : 'text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300'}
              `}
            >
              {arch}
            </button>
          ))}
        </div>
      )}

      <div className="flex-grow" />

      <button
        className={`
          w-full py-3 px-4 rounded-xl flex items-center justify-center gap-2 font-medium transition-all
          ${isDownloadable
            ? 'bg-neutral-900 dark:bg-white text-white dark:text-black hover:opacity-90 active:scale-[0.98]' 
            : 'bg-neutral-100 dark:bg-neutral-900 text-neutral-600 dark:text-neutral-400 border border-neutral-200 dark:border-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-800'}
        `}
      >
        {isDownloadable ? (
          <Download className="w-4 h-4" />
        ) : (
          <AlertCircle className="w-4 h-4 text-[#F08787]" />
        )}
        <span>{platform.primaryAction?.label || 'Coming Soon'}</span>
      </button>

      {platform.primaryAction?.subLabel && (
        <p className="text-xs text-center text-neutral-400 mt-3 font-mono">
          {platform.primaryAction.subLabel}
        </p>
      )}
    </motion.div>
  );
}