"use client"

import { Play } from "lucide-react"
import { useState } from "react"

export default function Demo() {
  const [isPlaying, setIsPlaying] = useState(false)

  return (
    <section className="relative py-24 px-4">
      <div className="max-w-5xl mx-auto">
        
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-foreground">
            See Engram in <span className="neon-purple">Action</span>
          </h2>
          <p className="text-lg text-muted-foreground">Watch how intuitive and powerful local-first AI can be</p>
        </div>

        {/* Video container */}
        <div className="relative group">
          
          <div className="absolute -inset-1 bg-gradient-to-r from-primary via-accent to-primary rounded-lg blur opacity-30 group-hover:opacity-50 transition duration-300"></div>

          
          <div className="relative rounded-lg overflow-hidden border border-primary/50 bg-card/30 backdrop-blur-sm">
           
            <div className="aspect-video bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center relative overflow-hidden">
              
              <div className="absolute inset-0 opacity-10 grid-bg"></div>

              
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="relative z-10 w-20 h-20 rounded-full bg-primary/90 hover:bg-primary transition-all duration-300 flex items-center justify-center group/play shadow-lg hover:shadow-primary/50"
              >
                <Play className="w-8 h-8 text-primary-foreground ml-1" fill="currentColor" />
              </button>

              
              <div className="absolute bottom-6 left-6 right-6 z-10">
                <p className="text-foreground text-sm font-medium">Engram Demo: Local AI in Motion</p>
                <p className="text-muted-foreground text-xs mt-1">5 minutes • No account required</p>
              </div>
            </div>
          </div>
        </div>

        
        <div className="mt-12 text-center">
          <button className="px-6 py-2 rounded-full bg-primary/10 border border-primary/40 text-primary hover:bg-primary/20 transition-colors text-sm font-medium">
            Download Engram Today
          </button>
        </div>
      </div>
    </section>
  )
}
