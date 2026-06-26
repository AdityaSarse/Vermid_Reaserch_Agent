import React from 'react';

export default function ScoreBadge({ label, value }) {
  return (
    <div className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#FAFAFA] border border-[#E5E5E5] text-[11px]">
      <span className="text-[#999999] font-normal">{label}</span>
      <span className="font-mono font-medium text-[#111111]">
        {value !== null && value !== undefined ? value.toFixed(4) : '0.0000'}
      </span>
    </div>
  );
}
