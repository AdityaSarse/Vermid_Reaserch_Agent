import React from 'react';

export default function ScoreBadge({ label, value }) {
  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#252525] border border-[#2a2a2a] text-[11.5px]">
      <span className="text-[#666666] font-normal">{label}</span>
      <span className="font-mono font-medium text-white">
        {value !== null && value !== undefined ? value.toFixed(4) : '0.0000'}
      </span>
    </div>
  );
}
