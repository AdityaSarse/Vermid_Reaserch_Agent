import React from 'react';

export default function ScoreBadge({ label, value, type }) {
  let scoreColorClass = 'text-indigo-400 border-indigo-500/25 bg-indigo-500/5';
  
  if (type === 'hybrid') {
    if (value >= 0.7) {
      scoreColorClass = 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
    } else if (value >= 0.4) {
      scoreColorClass = 'text-amber-400 border-amber-500/30 bg-amber-500/10';
    } else {
      scoreColorClass = 'text-slate-400 border-slate-500/20 bg-slate-500/5';
    }
  } else if (type === 'bm25') {
    scoreColorClass = 'text-sky-400 border-sky-500/20 bg-sky-500/5';
  } else if (type === 'semantic') {
    scoreColorClass = 'text-purple-400 border-purple-500/20 bg-purple-500/5';
  }

  return (
    <div className={`flex flex-col items-center justify-center px-3 py-1.5 rounded-lg border ${scoreColorClass} backdrop-blur-md transition-all duration-200 hover:brightness-110`}>
      <span className="text-[9px] uppercase tracking-widest font-bold opacity-70">{label}</span>
      <span className="text-sm font-extrabold font-mono mt-0.5">
        {value !== null && value !== undefined ? value.toFixed(4) : '0.0000'}
      </span>
    </div>
  );
}
