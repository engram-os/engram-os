import { Lock, Mic, Brain } from "lucide-react"

export default function Features() {
  const features = [
    {
      icon: Lock,
      title: "Privacy First",
      description:
        "Your data never leaves your device. No cloud sync, no analytics, no tracking. True privacy by design.",
      color: "from-primary to-primary/50",
    },
    {
      icon: Mic,
      title: "Voice Interaction",
      description: "Natural voice commands with real-time processing. Speak, don't type. Perfectly understood.",
      color: "from-accent to-accent/50",
    },
    {
      icon: Brain,
      title: "Long-Term Memory",
      description: "AI that remembers context from your entire history. Smart, personalized, and genuinely helpful.",
      color: "from-primary/70 to-accent/70",
    },
  ]

  return (
    <section className="relative py-24 px-4">
      <div className="max-w-6xl mx-auto">
        
        <div className="text-center mb-20">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-foreground">
            Built for <span className="neon-purple">Intelligence</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Three core capabilities that make Engram the OS you've always wanted
          </p>
        </div>

        
        <div className="grid md:grid-cols-3 gap-6">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div
                key={index}
                className="group relative p-8 rounded-lg border border-glow border-primary/30 bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-all duration-300 hover:border-primary/60 hover:shadow-lg hover:shadow-primary/20"
              >
                
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-primary to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-t-lg"></div>

                
                <div className="mb-6 inline-block p-3 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                  <Icon className="w-6 h-6 text-primary" />
                </div>

                
                <h3 className="text-xl font-bold mb-3 text-foreground">{feature.title}</h3>
                <p className="text-muted-foreground leading-relaxed">{feature.description}</p>

                
                <div className="mt-6 flex items-center text-primary text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                  <span>Learn more</span>
                  <svg
                    className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
