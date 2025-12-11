'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Book, Cpu, Shield, Terminal, Zap } from 'lucide-react';

const sidebarLinks = [
  {
    category: "Getting Started",
    items: [
      { label: "Introduction", href: "/docs", icon: Book },
      { label: "Installation", href: "/docs/installation", icon: Zap },
      { label: "Architecture", href: "/docs/architecture", icon: Cpu },
    ]
  },
  {
    category: "Core Concepts",
    items: [
      { label: "The Memory Graph", href: "/docs/memory-graph", icon: Terminal },
      { label: "Privacy Model", href: "/docs/privacy", icon: Shield },
    ]
  }
];

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[#FAFAFA] dark:bg-[#0A0A0A] pt-20">
      
      <aside className="fixed top-20 bottom-0 left-0 z-20 hidden md:flex w-64 xl:w-72 flex-col overflow-y-auto border-r border-neutral-200 dark:border-neutral-800 bg-[#FAFAFA] dark:bg-[#0A0A0A] px-6 py-10">
        <div className="space-y-8">
          {sidebarLinks.map((section) => (
            <div key={section.category}>
              <h4 className="mb-3 px-2 text-xs font-mono font-semibold uppercase tracking-wider text-neutral-500">
                {section.category}
              </h4>
              <ul className="space-y-1">
                {section.items.map((item) => {
                  const isActive = pathname === item.href;
                  return (
                    <li key={item.href}>
                      <Link 
                        href={item.href}
                        className={`
                          group flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-all duration-200
                          ${isActive 
                            ? 'bg-neutral-100 dark:bg-neutral-900 text-[#F08787] font-medium' 
                            : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200'}
                        `}
                      >
                        <item.icon className={`w-4 h-4 transition-colors ${isActive ? 'text-[#F08787]' : 'text-neutral-400 group-hover:text-neutral-600'}`} />
                        {item.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      </aside>

      <main className="md:pl-64 xl:pl-72 flex min-h-[calc(100vh-80px)] flex-col">
        
        <div className="w-full max-w-3xl mx-auto px-6 py-12 md:py-20 lg:px-12">
          {children}
        </div>
        
      </main>
    </div>
  );
}