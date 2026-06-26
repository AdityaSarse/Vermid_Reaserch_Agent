import React from 'react';

const SUGGESTIONS = [
  "Can Metformin cause Vitamin B12 deficiency?",
  "Efficacy of immunotherapy in early-stage NSCLC",
  "Proton pump inhibitors long-term vitamin B12 absorption",
  "Genetic risk factors for metformin-induced cobalamin deficiency"
];

export default function SearchBar({ query, setQuery, onSearch, isLoading }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
    onSearch(suggestion);
  };

  return (
    <div className="w-full max-w-3xl mx-auto flex flex-col gap-3">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            value={query || ''}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type your medical query (e.g., Metformin vitamin B12 deficiency...)"
            disabled={isLoading}
            className="w-full bg-slate-900/40 hover:bg-slate-900/60 focus:bg-slate-900/80 text-slate-100 placeholder-slate-500 border border-slate-850 focus:border-indigo-500/60 rounded-xl px-5 py-4 pl-12 text-base outline-none transition-all duration-200 shadow-md focus:shadow-indigo-500/5 focus:ring-1 focus:ring-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          />
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
          </div>
        </div>
        <button
          type="submit"
          disabled={isLoading || !query?.trim()}
          className="bg-indigo-600 hover:bg-indigo-550 active:bg-indigo-700 text-white font-semibold px-6 py-4 rounded-xl shadow-md shadow-indigo-600/10 hover:shadow-indigo-500/15 active:shadow-indigo-700/5 transition-all duration-205 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-base whitespace-nowrap"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Searching...
            </>
          ) : (
            <>
              Search
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
              </svg>
            </>
          )}
        </button>
      </form>
      
      <div className="flex flex-col gap-1.5 mt-1">
        <span className="text-[9px] text-slate-500 uppercase tracking-widest font-extrabold pl-1">Suggested Queries:</span>
        <div className="flex flex-wrap gap-2">
          {SUGGESTIONS.map((suggestion, index) => (
            <button
              key={index}
              type="button"
              onClick={() => handleSuggestionClick(suggestion)}
              disabled={isLoading}
              className="text-xs text-left bg-slate-900/30 hover:bg-indigo-500/10 hover:text-indigo-300 border border-slate-800/60 hover:border-indigo-500/20 px-3.5 py-1.5 rounded-full cursor-pointer transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed select-none truncate max-w-full font-medium"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
