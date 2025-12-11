'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, Lock, FileText, CheckCircle } from 'lucide-react';

const legalLinks = [
  { name: 'Privacy Policy', href: '/legal/privacy', icon: Lock },
  { name: 'Terms of Service', href: '/legal/terms', icon: FileText },
  { name: 'Security Audit', href: '/legal/security', icon: Shield },
  { name: 'DPA', href: '/legal/dpa', icon: CheckCircle },
];

export default function LegalLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen pt-32 pb-20 px-6 bg-[#FAFAFA] dark:bg-[#0A0A0A]">
      <div className="max-w-5xl mx-auto flex flex-col md:flex-row gap-12">
        
        <aside className="w-full md:w-64 shrink-0">
           <div className="sticky top-32">
            <h3 className="font-mono text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-4 px-3">
              Legal Center
            </h3>
            <nav className="space-y-1">
              {legalLinks.map((link) => {
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`
                      flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors
                      ${isActive 
                        ? 'bg-neutral-100 dark:bg-neutral-900 text-[#F08787]' 
                        : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200'}
                    `}
                  >
                    <link.icon className="w-4 h-4" />
                    {link.name}
                  </Link>
                );
              })}
            </nav>
          </div>
        </aside>

        <main className="flex-1 min-w-0">
          <div className={`
            prose max-w-none 
            
            /* Light Mode Defaults */
            prose-neutral 
            prose-headings:text-neutral-900 
            prose-p:text-neutral-700
            prose-strong:text-neutral-900
            prose-li:text-neutral-700
            
            /* Dark Mode Overrides */
            dark:prose-invert 
            dark:prose-headings:text-white 
            dark:prose-p:text-neutral-300 
            dark:prose-strong:text-white
            dark:prose-li:text-neutral-300
            dark:prose-blockquote:text-neutral-300
            
            /* Shared Styles */
            prose-headings:font-bold 
            prose-a:text-[#F08787] 
            prose-img:rounded-xl
          `}>
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}