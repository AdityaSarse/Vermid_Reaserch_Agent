import React, { useState } from 'react';
import ScoreBadge from './ScoreBadge';

export default function PaperCard({ paper }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatAuthors = (authors) => {
    if (!authors || authors.length === 0) return 'Unknown Authors';
    if (authors.length <= 3) return authors.join(', ');
    return `${authors.slice(0, 3).join(', ')} et al.`;
  };

  return (
    <div className="group relative bg-slate-900/30 hover:bg-slate-900/60 border border-slate-800/80 hover:border-slate-700/60 rounded-xl p-5 md:p-6 transition-all duration-300 shadow-md hover:shadow-indigo-500/5 flex flex-col gap-4 overflow-hidden">
      {/* Background radial glow on hover */}
      <div className="absolute -inset-px bg-gradient-to-r from-indigo-500/0 to-indigo-500/0 group-hover:from-indigo-500/5 group-hover:to-purple-500/5 rounded-xl transition-all duration-300 pointer-events-none" />

      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 z-10">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1.5">
            {paper.year && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-800 text-indigo-300 border border-indigo-500/10">
                {paper.year}
              </span>
            )}
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium bg-slate-800 text-slate-400">
              PMID: {paper.pmid}
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-100 group-hover:text-indigo-300 transition-colors duration-200 leading-snug">
            <a 
              href={`https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}`} 
              target="_blank" 
              rel="noreferrer"
              className="hover:underline flex items-center gap-1 inline-flex flex-wrap"
            >
              {paper.title}
              <svg className="w-3.5 h-3.5 opacity-0 group-hover:opacity-75 transition-opacity inline" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
              </svg>
            </a>
          </h3>
          <p className="text-xs text-slate-400 font-medium mt-1.5">
            {formatAuthors(paper.authors)}
          </p>
        </div>

        {/* Score Badges */}
        <div className="flex items-center gap-2 self-start md:self-auto flex-wrap">
          <ScoreBadge label="BM25" value={paper.bm25_score} type="bm25" />
          <ScoreBadge label="Semantic" value={paper.semantic_score} type="semantic" />
          <ScoreBadge label="Hybrid" value={paper.score} type="hybrid" />
        </div>
      </div>

      {/* Abstract */}
      <div className="z-10 flex-1">
        {paper.abstract ? (
          <div>
            <div className={`text-sm text-slate-300 leading-relaxed overflow-hidden transition-all duration-300 ${isExpanded ? 'max-h-[1000px]' : 'max-h-[72px]'}`}>
              {paper.abstract}
            </div>
            {paper.abstract.length > 200 && (
              <button 
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold mt-2 focus:outline-none flex items-center gap-1 transition-colors"
              >
                {isExpanded ? (
                  <>
                    Collapse Abstract
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7"></path></svg>
                  </>
                ) : (
                  <>
                    Read Full Abstract
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                  </>
                )}
              </button>
            )}
          </div>
        ) : (
          <p className="text-sm italic text-slate-500">No abstract available for this article.</p>
        )}
      </div>
    </div>
  );
}
