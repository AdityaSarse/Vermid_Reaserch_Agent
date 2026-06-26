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
    <div className="min-h-screen bg-white text-[#111111] flex flex-col font-sans antialiased">
      <div className="max-w-[720px] w-full mx-auto px-4 py-8 flex flex-col gap-6 flex-grow">
        
        {/* Top Header Row */}
        <header className="flex justify-between items-center text-[12px] text-[#999999] tracking-tight">
          <span className="font-normal">VeriMed-X · Research Agent</span>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-[#FAFAFA] border border-[#E5E5E5] text-[10px] font-medium tracking-normal select-none">
            <span className={`w-1.5 h-1.5 rounded-full ${
              apiStatus === 'online' ? 'bg-emerald-500 pulse-active' :
              apiStatus === 'offline' ? 'bg-rose-500' : 'bg-amber-500 animate-pulse'
            }`} />
            <span>SYSTEM STATUS · {apiStatus === 'online' ? 'ONLINE' : apiStatus === 'offline' ? 'OFFLINE' : 'CHECKING'}</span>
          </div>
        </header>

        {/* Hero Section */}
        <section className="flex flex-col gap-2 mt-4">
          <h1 className="text-[28px] font-medium text-[#111111] tracking-tight leading-tight">
            What do you want to know?
          </h1>
          <p className="text-[14px] text-[#666666] leading-relaxed">
            Search 35M+ PubMed publications with hybrid semantic ranking
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

        {/* Divider and Results Header */}
        {(latency || papers.length > 0) && !isLoading && (
          <section className="w-full mt-2">
            <div className="flex items-center justify-between border-b border-[#E5E5E5] pb-2 text-[13px] text-[#666666]">
              <div>
                {papers.length} publications for <span className="text-[#111111] font-medium">"{searchedQuery}"</span>
              </div>
              <div className="flex items-center gap-3">
                {latency && <span className="font-mono text-[12px]">{latency}s</span>}
                <span className="flex items-center gap-1 select-none font-medium text-[#111111]">
                  {source === 'cached' ? '⚡ cached' : '🔍 PubMed'}
                </span>
              </div>
            </div>
          </section>
        )}

        {/* Results / Loading / Error List */}
        <section className="w-full flex-1 flex flex-col gap-4 mt-2">
          {isLoading && <LoadingSkeleton />}

          {error && (
            <div className="bg-[#FFF5F5] border border-[#FEE2E2] text-rose-800 rounded-[12px] p-5 text-center flex flex-col items-center gap-2">
              <h4 className="text-[14px] font-medium">Search Failed</h4>
              <p className="text-[13px] text-rose-750 max-w-md leading-relaxed">
                {error}
              </p>
            </div>
          )}

          {!isLoading && !error && papers.length === 0 && searchedQuery && (
            <div className="bg-[#FAFAFA] border border-[#E5E5E5] rounded-[12px] p-8 text-center flex flex-col items-center gap-1.5">
              <h4 className="text-[14px] font-medium text-[#111111]">No Publications Found</h4>
              <p className="text-[13px] text-[#666666] max-w-sm leading-relaxed">
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

        {/* Small Bottom Margin */}
        <footer className="h-8" />
      </div>
    </div>
  );
}

// Skeleton loading cards matching the minimal design
const LoadingSkeleton = () => (
  <div className="flex flex-col gap-4 w-full">
    {[1, 2, 3].map((i) => (
      <div key={i} className="animate-pulse bg-[#FAFAFA] border border-[#E5E5E5] rounded-[12px] p-5 flex flex-col gap-3.5">
        <div className="flex gap-2">
          <div className="h-4 w-12 bg-[#E5E5E5] rounded-full"></div>
          <div className="h-4 w-24 bg-[#E5E5E5] rounded-full"></div>
        </div>
        <div className="h-5 w-3/4 bg-[#E5E5E5] rounded"></div>
        <div className="h-4 w-1/2 bg-[#E5E5E5] rounded"></div>
        <div className="space-y-2 pt-2 border-t border-[#E5E5E5]/20">
          <div className="h-3 w-full bg-[#E5E5E5] rounded"></div>
          <div className="h-3 w-full bg-[#E5E5E5] rounded"></div>
          <div className="h-3 w-2/3 bg-[#E5E5E5] rounded"></div>
        </div>
      </div>
    ))}
  </div>
);
