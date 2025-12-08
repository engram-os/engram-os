"use client"

import { useState } from "react"

export default function Hero() {
  const [isHovering, setIsHovering] = useState(false)

  return (
    <section className="relative min-h-screen flex items-center justify-center px-4 py-20">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl opacity-30"></div>
        <div className="absolute bottom-20 right-1/4 w-96 h-96 bg-accent/10 rounded-full blur-3xl opacity-30"></div>
      </div>

      <div className="relative z-10 max-w-4xl mx-auto text-center">
        
        <div className="inline-block mb-8 px-4 py-2 rounded-full border border-primary/50 text-primary text-sm font-medium">
          <span className="neon-purple">✦ The Future of Computing</span>
        </div>

       
        <h1 className="text-5xl md:text-7xl font-bold mb-6 text-foreground tracking-tight text-balance">
          Your AI, <span className="neon-purple">On Your Device</span>
        </h1>

        
        <p className="text-lg md:text-xl text-muted-foreground mb-12 max-w-2xl mx-auto text-balance leading-relaxed">
          Engram is a local-first AI operating system. All your data stays with you. Complete privacy. Complete control.
        </p>

        
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <button
            onMouseEnter={() => setIsHovering(true)}
            onMouseLeave={() => setIsHovering(false)}
            className="px-8 py-3 rounded-full bg-primary text-primary-foreground font-semibold text-lg transition-all duration-300 hover:shadow-lg hover:shadow-primary/50 border border-primary"
          >
            Download Now
          </button>
          <button className="px-8 py-3 rounded-full bg-transparent text-foreground font-semibold text-lg border border-primary/40 hover:border-primary/70 transition-colors hover:bg-primary/5">
            Watch Demo
          </button>
        </div>

        
        <div className="mt-20 flex flex-col sm:flex-row gap-8 justify-center items-center text-sm text-muted-foreground">
          <div className="text-center">
            <div className="text-2xl font-bold neon-purple mb-1">100%</div>
            <div>Local Processing</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold neon-purple mb-1">0 KB</div>
            <div>Cloud Sent</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold neon-purple mb-1">∞</div>
            <div>Privacy Guaranteed</div>
          </div>
        </div>
      </div>
    </section>
  )
}
