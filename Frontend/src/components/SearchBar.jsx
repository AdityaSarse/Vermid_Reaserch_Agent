import React from 'react';

export default function SearchBar({ query, setQuery, onSearch, isLoading }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
    }
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            value={query || ''}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type your medical query..."
            disabled={isLoading}
            className="w-full bg-[#1a1a1a] text-white placeholder-[#666666] border border-[#2a2a2a] focus:border-[#4a9eff] rounded-[10px] px-4 py-3.5 pl-10 text-[14px] outline-none transition-all duration-205 disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#666666]">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
          </div>
        </div>
        <button
          type="submit"
          disabled={isLoading || !query?.trim()}
          className="bg-[#111111] hover:bg-[#1a1a1a] active:bg-black text-white border border-[#3a3a3a] px-6 py-3.5 rounded-full transition-colors duration-150 flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-[14px] font-medium whitespace-nowrap"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Searching
            </>
          ) : (
            'Search'
          )}
        </button>
      </form>
    </div>
  );
}
