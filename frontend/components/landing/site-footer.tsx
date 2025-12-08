"use client";

import { useState, useEffect, useRef } from "react";
import { motion, useMotionTemplate, useMotionValue } from "framer-motion";
import InstallModal from "@/components/ui/install-modal";
import { 
  Github, 
  Twitter, 
  Linkedin, 
  ArrowRight, 
  Cpu, 
  ShieldCheck, 
  Zap,
  Terminal
} from "lucide-react";

export default function SiteFooter() {
  const [time, setTime] = useState<string>("");
  const [installOpen, setInstallOpen] = useState(false);

  useEffect(() => {
    setTime(new Date().toISOString().split('T')[1].split('.')[0] + " UTC");
    const interval = setInterval(() => {
      setTime(new Date().toISOString().split('T')[1].split('.')[0] + " UTC");
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <footer className="bg-white pt-24 pb-12">
      <div className="container mx-auto px-6">
        
        <div className="mb-20">
            <SpotlightCard>
                <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">
                    <div className="space-y-4 max-w-xl">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#F08787]/10 text-[#F08787] text-xs font-mono font-bold border border-[#F08787]/20">
                            <Terminal size={12} />
                            <span>v1.0.4-beta Available</span>
                        </div>
                        <h2 className="text-4xl md:text-5xl font-bold text-white tracking-tight">
                            Ready to go dark?
                        </h2>
                        <p className="text-gray-400 text-lg">
                            Join 10,000+ engineers reclaiming their digital sovereignty. 
                            Open source, local-first, and forever private.
                        </p>
                    </div>
                    
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => setInstallOpen(true)}
                    
                        className="group relative inline-flex items-center justify-center gap-3 px-8 py-4 bg-white text-black rounded-xl font-bold text-lg overflow-hidden transition-all hover:bg-[#F08787] hover:text-white whitespace-nowrap shrink-0"
                    >
                        <span>Install Engram</span>
                        <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                    </motion.button>
                </div>

                
                <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10 pointer-events-none" />
                <div className="absolute inset-0 bg-grid-white/[0.05] pointer-events-none" />
            </SpotlightCard>
        </div>

        <InstallModal isOpen={installOpen} onClose={() => setInstallOpen(false)} />

        
        <div className="grid grid-cols-2 md:grid-cols-12 gap-8 mb-16 border-b border-gray-100 pb-16">
            <div className="col-span-2 md:col-span-4 space-y-4">
                <div className="flex items-center gap-2 font-bold text-xl">
                    <div className="w-8 h-8 bg-[#F08787] rounded-lg flex items-center justify-center text-white text-sm">E</div>
                    <span>Engram</span>
                </div>
                <p className="text-gray-500 text-sm max-w-xs">
                    The local-first AI operating system. 
                    Engineered for high-liability environments where data privacy is non-negotiable.
                </p>
                <div className="flex gap-4 pt-2">
                    <SocialIcon icon={Github} href="#" />
                    <SocialIcon icon={Twitter} href="#" />
                    <SocialIcon icon={Linkedin} href="#" />
                </div>
            </div>

            
            <div className="col-span-1 md:col-span-2 space-y-4">
                <h4 className="font-bold text-gray-900 text-sm">Product</h4>
                <ul className="space-y-3 text-sm text-gray-500">
                    <FooterLink href="#">Download</FooterLink>
                    <FooterLink href="#">Changelog</FooterLink>
                    <FooterLink href="#">Documentation</FooterLink>
                    <FooterLink href="#">Integrations</FooterLink>
                </ul>
            </div>

            <div className="col-span-1 md:col-span-2 space-y-4">
                <h4 className="font-bold text-gray-900 text-sm">Community</h4>
                <ul className="space-y-3 text-sm text-gray-500">
                    <FooterLink href="#">GitHub Discussions</FooterLink>
                    <FooterLink href="#">Discord</FooterLink>
                    <FooterLink href="#">Contributing</FooterLink>
                    <FooterLink href="#">Events</FooterLink>
                </ul>
            </div>

            <div className="col-span-1 md:col-span-2 space-y-4">
                <h4 className="font-bold text-gray-900 text-sm">Legal</h4>
                <ul className="space-y-3 text-sm text-gray-500">
                    <FooterLink href="#">Privacy Policy</FooterLink>
                    <FooterLink href="#">Terms of Service</FooterLink>
                    <FooterLink href="#">Security Audit</FooterLink>
                    <FooterLink href="#">DPA</FooterLink>
                </ul>
            </div>
        </div>

        
        <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-xs font-mono text-gray-400">
            <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                    <div className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </div>
                    <span className="text-green-600 font-semibold">Systems Normal</span>
                </div>
                <div className="flex items-center gap-2">
                    <Cpu size={12} />
                    <span>v1.0.4</span>
                </div>
                <div className="flex items-center gap-2">
                    <ShieldCheck size={12} />
                    <span>Audited</span>
                </div>
            </div>

            <div className="flex items-center gap-6">
                <div className="hidden md:block opacity-50">
                    {time || "Loading time..."}
                </div>
                <div>
                    &copy; 2025 Engram Inc.
                </div>
            </div>
        </div>

      </div>
    </footer>
  );
}



function FooterLink({ href, children }: { href: string; children: React.ReactNode }) {
    return (
        <li>
            <a href={href} className="hover:text-[#F08787] transition-colors flex items-center gap-1 group">
                {children}
            </a>
        </li>
    )
}

function SocialIcon({ icon: Icon, href }: { icon: any, href: string }) {
    return (
        <a href={href} className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-[#F08787] hover:text-white transition-all">
            <Icon size={18} />
        </a>
    )
}


function SpotlightCard({ children }: { children: React.ReactNode }) {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  function handleMouseMove({ currentTarget, clientX, clientY }: React.MouseEvent) {
    const { left, top } = currentTarget.getBoundingClientRect();
    mouseX.set(clientX - left);
    mouseY.set(clientY - top);
  }

  return (
    <div
      className="group relative border border-gray-800 bg-[#1a1a1a] overflow-hidden rounded-3xl p-8 md:p-12"
      onMouseMove={handleMouseMove}
    >
      <motion.div
        className="pointer-events-none absolute -inset-px rounded-3xl opacity-0 transition duration-300 group-hover:opacity-100"
        style={{
          background: useMotionTemplate`
            radial-gradient(
              650px circle at ${mouseX}px ${mouseY}px,
              rgba(240, 135, 135, 0.15),
              transparent 80%
            )
          `,
        }}
      />
      {children}
    </div>
  );
}