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
  const [source, setSource] = useState('pubmed'); // 'pubmed' | 'cached'

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
      setSource(data.source || 'pubmed');
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to connect to the research server. Please ensure the backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-white flex flex-col font-sans antialiased">
      
      {/* Fixed Top Right Status Indicator */}
      <div className="fixed top-6 right-6 z-50 flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#181818] border border-[#2a2a2a] text-[10px] font-medium tracking-wider text-[#666666] select-none">
        <span className={`w-1.5 h-1.5 rounded-full ${
          apiStatus === 'online' ? 'bg-[#22c55e] pulse-active' :
          apiStatus === 'offline' ? 'bg-rose-500' : 'bg-amber-500 animate-pulse'
        }`} />
        <span>SYSTEM STATUS · {apiStatus === 'online' ? 'ONLINE' : apiStatus === 'offline' ? 'OFFLINE' : 'CHECKING'}</span>
      </div>

      <div className="max-w-[720px] w-full mx-auto px-4 py-12 flex flex-col gap-6 flex-grow">
        
        {/* Top Center Label */}
        <div className="text-center">
          <span className="text-[11px] uppercase tracking-[0.15em] text-[#666666] font-medium">
            VERIMED-X · RESEARCH AGENT
          </span>
        </div>

        {/* Hero Section */}
        <section className="flex flex-col gap-2 text-center mt-6 mb-2">
          <h1 className="text-[32px] font-semibold text-white tracking-tight leading-tight">
            What do you want to know?
          </h1>
          <p className="text-[14px] text-[#666666] leading-relaxed">
            Search 35M+ PubMed publications with hybrid semantic ranking
          </p>
        </section>

        {/* Search Bar Section */}
        <section className="w-full mb-2">
          <SearchBar 
            query={query} 
            setQuery={setQuery} 
            onSearch={handleSearch} 
            isLoading={isLoading} 
          />
        </section>

        {/* Results Header */}
        {(latency || papers.length > 0) && !isLoading && (
          <section className="w-full">
            <div className="flex items-center justify-between text-[13px] text-[#666666]">
              <div>
                <span className="font-semibold text-white">{papers.length} publications</span>{' '}
                <span>for "{searchedQuery}"</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#22c55e]" />
                <span>
                  {latency}s · {source === 'cached' ? 'FAISS cache' : 'PubMed API'}
                </span>
              </div>
            </div>
          </section>
        )}

        {/* Results / Loading / Error List */}
        <section className="w-full flex-1 flex flex-col gap-2">
          {isLoading && <LoadingSkeleton />}

          {error && (
            <div className="bg-[#1a1313] border border-rose-950/50 text-rose-450 rounded-[10px] p-5 text-center flex flex-col items-center gap-2">
              <h4 className="text-[14px] font-semibold text-rose-200">Search Failed</h4>
              <p className="text-[13px] text-rose-350 max-w-md leading-relaxed">
                {error}
              </p>
            </div>
          )}

          {!isLoading && !error && papers.length === 0 && searchedQuery && (
            <div className="bg-[#181818] border border-[#2a2a2a] rounded-[10px] p-8 text-center flex flex-col items-center gap-1.5">
              <h4 className="text-[14px] font-semibold text-white">No Publications Found</h4>
              <p className="text-[13px] text-[#666666] max-w-sm leading-relaxed">
                No matching articles found on PubMed or local store. Try checking the query spelling or using broader terms.
              </p>
            </div>
          )}

          {!isLoading && !error && papers.length > 0 && (
            <div className="flex flex-col gap-2">
              {papers.map((paper) => (
                <PaperCard key={paper.pmid} paper={paper} />
              ))}
            </div>
          )}
        </section>

        {/* Small Bottom Margin */}
        <footer className="h-8" />
      </div>
    </div>
  );
}

// Skeleton loading cards matching the minimal dark design
const LoadingSkeleton = () => (
  <div className="flex flex-col gap-2 w-full">
    {[1, 2, 3].map((i) => (
      <div key={i} className="animate-pulse bg-[#181818] border border-[#2a2a2a] rounded-[10px] p-5 flex flex-col gap-3.5">
        <div className="flex gap-2">
          <div className="h-4 w-12 bg-[#252525] rounded-full"></div>
          <div className="h-4 w-24 bg-[#252525] rounded-full"></div>
        </div>
        <div className="h-5 w-3/4 bg-[#252525] rounded"></div>
        <div className="h-4 w-1/2 bg-[#252525] rounded"></div>
        <div className="space-y-2 pt-2 border-t border-[#2a2a2a]/20">
          <div className="h-3 w-full bg-[#252525] rounded"></div>
          <div className="h-3 w-full bg-[#252525] rounded"></div>
          <div className="h-3 w-2/3 bg-[#252525] rounded"></div>
        </div>
      </div>
    ))}
  </div>
);
