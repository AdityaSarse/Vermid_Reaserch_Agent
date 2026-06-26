import { useState, useEffect } from 'react';
import SearchBar from './components/SearchBar';
import PaperCard from './components/PaperCard';

export default function App() {
  const [query, setQuery] = useState('');
  const [papers, setPapers] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [latency, setLatency] = useState(null);
  const [apiStatus, setApiStatus] = useState('checking'); // 'checking' | 'online' | 'offline'
  const [searchedQuery, setSearchedQuery] = useState('');

  // Perform a health check on the FastAPI backend at startup
  useEffect(() => {
    const checkHealth = () => {
      fetch('http://127.0.0.1:8000/health')
        .then((res) => {
          if (!res.ok) throw new Error('API down');
          return res.json();
        })
        .then((data) => {
          if (data.status === 'healthy') {
            setApiStatus('online');
          } else {
            setApiStatus('offline');
          }
        })
        .catch(() => {
          setApiStatus('offline');
        });
    };
    checkHealth();
    // Poll health status every 15 seconds
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleSearch = async (searchQuery) => {
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    setError(null);
    setPapers([]);
    setLatency(null);
    setSearchedQuery(searchQuery);

    const startTime = performance.now();

    try {
      const response = await fetch('http://127.0.0.1:8000/research', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: searchQuery }),
      });

      const endTime = performance.now();
      const elapsed = ((endTime - startTime) / 1000).toFixed(2);
      setLatency(elapsed);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Search failed with status ${response.status}`);
      }

      const data = await response.json();
      setPapers(data.papers || []);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to connect to the research server. Please ensure the backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100 flex flex-col font-sans select-none antialiased">
      {/* Background Decorative Blobs */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-500/5 rounded-full filter blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full filter blur-3xl pointer-events-none" />

      {/* Header / Navbar */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/80 border-b border-slate-900/80 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-600/20">
              <svg className="w-5.5 h-5.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path>
              </svg>
            </div>
            <div>
              <span className="font-extrabold text-sm tracking-wider uppercase text-slate-200">VeriMed-X</span>
              <div className="text-[10px] text-indigo-400 font-bold tracking-widest uppercase -mt-1">Research Agent</div>
            </div>
          </div>

          {/* Backend Status indicator */}
          <div className="flex items-center gap-2 bg-slate-900/60 border border-slate-800/80 px-3 py-1.5 rounded-lg">
            <span className="text-[10px] font-bold text-slate-400 tracking-wider uppercase">System Status:</span>
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${
                apiStatus === 'online' ? 'bg-emerald-500 pulse-active' :
                apiStatus === 'offline' ? 'bg-rose-500' : 'bg-amber-500 animate-pulse'
              }`} />
              <span className="text-[10px] font-extrabold uppercase tracking-widest text-slate-350">
                {apiStatus === 'online' ? 'Online' :
                 apiStatus === 'offline' ? 'Offline' : 'Checking'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-10 flex flex-col gap-10">
        
        {/* Hero Section */}
        <section className="text-center flex flex-col gap-4">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-300 bg-clip-text text-transparent">
            Medical Search & Re-Ranking
          </h1>
          <p className="max-w-2xl mx-auto text-sm md:text-base text-slate-400 leading-relaxed font-medium">
            Search PubMed publications using hybrid semantic algorithms. Matches keywords using <span className="text-sky-400 font-semibold">BM25</span>, computes semantic matches via <span className="text-purple-400 font-semibold">S-PubMedBert</span> embeddings, and caches queries locally in a <span className="text-indigo-400 font-semibold">FAISS</span> vector store.
          </p>
        </section>

        {/* Search Bar Section */}
        <section className="w-full">
          <SearchBar 
            query={query} 
            setQuery={setQuery} 
            onSearch={handleSearch} 
            isLoading={isLoading} 
          />
        </section>

        {/* Status / Latency Stats */}
        {(latency || papers.length > 0) && !isLoading && (
          <div className="flex items-center justify-between border-b border-slate-900 pb-3 text-xs text-slate-500 font-bold uppercase tracking-wider px-1">
            <div className="flex items-center gap-2">
              <span>Results for:</span>
              <span className="text-indigo-400 normal-case italic font-medium">"{searchedQuery}"</span>
            </div>
            <div className="flex items-center gap-4">
              <span>{papers.length} publications</span>
              {latency && (
                <span className="flex items-center gap-1">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  {latency}s latency
                </span>
              )}
            </div>
          </div>
        )}

        {/* Results / Skeleton / Error Panel */}
        <section className="w-full flex-1">
          {isLoading && <LoadingSkeleton />}

          {error && (
            <div className="bg-rose-950/20 border border-rose-500/20 rounded-xl p-6 text-center flex flex-col items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-rose-500/10 flex items-center justify-center text-rose-400">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                </svg>
              </div>
              <h4 className="text-base font-bold text-rose-200">Search Failed</h4>
              <p className="text-sm text-slate-400 max-w-md leading-relaxed font-medium">
                {error}
              </p>
            </div>
          )}

          {!isLoading && !error && papers.length === 0 && searchedQuery && (
            <div className="bg-slate-900/10 border border-slate-900/80 rounded-xl p-8 text-center flex flex-col items-center gap-2">
              <svg className="w-8 h-8 text-slate-600 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <h4 className="text-sm font-bold text-slate-450">No Publications Found</h4>
              <p className="text-xs text-slate-500 max-w-sm font-medium">
                No matching articles found on PubMed or local store. Try checking the query spelling or using broader terms.
              </p>
            </div>
          )}

          {!isLoading && !error && papers.length > 0 && (
            <div className="flex flex-col gap-4">
              {papers.map((paper) => (
                <PaperCard key={paper.pmid} paper={paper} />
              ))}
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900/80 py-6 px-6 text-center text-xs text-slate-650 font-medium">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© 2026 VeriMed-X Intelligent Medical Research Portal.</p>
          <div className="flex items-center gap-4 text-slate-500 font-semibold uppercase tracking-wider">
            <a href="https://pubmed.ncbi.nlm.nih.gov/" target="_blank" className="hover:text-indigo-400">NCBI PubMed</a>
            <span>•</span>
            <a href="https://huggingface.co/pritamdeka/S-PubMedBert-MS-MARCO" target="_blank" className="hover:text-indigo-400">PubMedBERT</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

// Skeleton loading cards for premium UI feedback
const LoadingSkeleton = () => (
  <div className="flex flex-col gap-4 w-full">
    {[1, 2, 3].map((i) => (
      <div key={i} className="animate-pulse bg-slate-900/10 border border-slate-850/80 rounded-xl p-5 md:p-6 flex flex-col gap-4">
        <div className="flex flex-col md:flex-row justify-between items-start gap-4">
          <div className="flex-1 w-full">
            <div className="flex gap-2 mb-2.5">
              <div className="h-4 w-12 bg-slate-800 rounded"></div>
              <div className="h-4 w-24 bg-slate-800 rounded"></div>
            </div>
            <div className="h-6 w-3/4 bg-slate-800 rounded mb-2.5"></div>
            <div className="h-4.5 w-1/2 bg-slate-800 rounded"></div>
          </div>
          <div className="flex gap-2">
            <div className="h-9 w-16 bg-slate-850 rounded-lg"></div>
            <div className="h-9 w-16 bg-slate-850 rounded-lg"></div>
            <div className="h-9 w-16 bg-slate-850 rounded-lg"></div>
          </div>
        </div>
        <div className="space-y-2.5">
          <div className="h-4 w-full bg-slate-850 rounded"></div>
          <div className="h-4 w-full bg-slate-850 rounded"></div>
          <div className="h-4 w-2/3 bg-slate-850 rounded"></div>
        </div>
      </div>
    ))}
  </div>
);
