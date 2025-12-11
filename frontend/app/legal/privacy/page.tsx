export default function PrivacyPage() {
  return (
    <article>
      <h1>Privacy Policy</h1>
      <p className="lead text-xl text-neutral-600 dark:text-neutral-400">
        Effective Date: December 10, 2025
      </p>

      <div className="p-6 my-8 rounded-xl bg-[#F08787]/10 border border-[#F08787]/20 text-[#F08787]">
        <h4 className="text-lg font-bold mb-2 flex items-center gap-2">
          tl;dr: We don't want your data.
        </h4>
        <p className="text-sm m-0">
          Engram is architected to be "Zero Knowledge." Your files, chats, and vector embeddings live on your machine. 
          We have no server-side access to your personal information.
        </p>
      </div>

      <h2>1. Data Collection</h2>
      <p>
        Unlike cloud-based AI services, Engram runs locally. This fundamentally changes the privacy model:
      </p>
      <ul>
        <li><strong>Content:</strong> We do not collect, store, or transmit your files (PDFs, Markdown) or chat history.</li>
        <li><strong>Inference:</strong> All AI processing is performed by local models (Llama 3 via Ollama). No text is sent to OpenAI or Anthropic.</li>
        <li><strong>Telemetry:</strong> We collect anonymous crash reports only if you explicitly opt-in during installation.</li>
      </ul>

      <h2>2. Third-Party Services</h2>
      <p>
        The only time your data leaves your device is when you explicitly use a "Cloud Bridge" integration:
      </p>
      <ul>
        <li><strong>GitHub Integration:</strong> Connects directly to GitHub API from your IP address. We do not proxy this traffic.</li>
        <li><strong>Google Calendar:</strong> Uses local OAuth tokens stored in your system keychain.</li>
      </ul>

      <h2>3. Data Deletion</h2>
      <p>
        Since we do not store your data, we cannot delete it for you. To delete your data, simply uninstall the application and remove the <code>~/.engram</code> directory from your computer.
      </p>

      <h2>4. Updates to Policy</h2>
      <p>
        We may update this policy to reflect changes in our optional cloud services. Major changes will be notified via the application update log.
      </p>
    </article>
  );
}