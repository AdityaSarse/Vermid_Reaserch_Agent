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
    <div className="bg-[#181818] border border-[#2a2a2a] rounded-[10px] p-5 flex flex-col gap-3.5 hover:border-[#444444] transition-all duration-200">
      {/* Top Row: Year, PMID, Cache Badge */}
      <div className="flex items-center gap-2 flex-wrap">
        {paper.year && (
          <span className="px-2.5 py-0.5 rounded-full border border-[#2a2a2a] text-[11px] text-[#666666] font-normal">
            {paper.year}
          </span>
        )}
        <span className="px-2.5 py-0.5 rounded-full border border-[#2a2a2a] text-[11px] text-[#666666] font-mono">
          PMID: {paper.pmid}
        </span>
        {paper.is_cached && (
          <span className="px-2.5 py-0.5 rounded-full bg-emerald-950/80 text-[#22c55e] border border-emerald-900/50 text-[11px] font-medium flex items-center gap-0.5 select-none">
            ⚡ cached
          </span>
        )}
      </div>

      {/* Title & Authors */}
      <div className="flex flex-col gap-1">
        <h3 className="text-[15px] font-semibold text-white leading-snug">
          <a
            href={`https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}`}
            target="_blank"
            rel="noreferrer"
            className="hover:underline line-clamp-2"
          >
            {paper.title}
          </a>
        </h3>
        <p className="text-[12px] text-[#666666]">
          {formatAuthors(paper.authors)}
        </p>
      </div>

      {/* Abstract Content */}
      {paper.abstract ? (
        <div className="text-[13px] text-[#aaaaaa] leading-relaxed">
          <div className={isExpanded ? '' : 'line-clamp-3'}>
            {paper.abstract}
          </div>
        </div>
      ) : (
        <p className="text-[13px] italic text-[#666666]">No abstract available for this article.</p>
      )}

      {/* Bottom Row */}
      <div className="flex items-center justify-between gap-4 flex-wrap pt-1.5 border-t border-[#2a2a2a]/30">
        {/* Score Badges */}
        <div className="flex items-center gap-2 flex-wrap">
          <ScoreBadge label="BM25" value={paper.bm25_score} />
          <ScoreBadge label="Semantic" value={paper.semantic_score} />
          <ScoreBadge label="Hybrid" value={paper.score} />
        </div>

        {/* Read abstract toggle link */}
        {paper.abstract && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-[13px] font-medium text-[#4a9eff] hover:underline focus:outline-none flex items-center gap-0.5 cursor-pointer"
          >
            {isExpanded ? 'Collapse abstract ↑' : 'Read abstract ↓'}
          </button>
        )}
      </div>
    </div>
  );
}
