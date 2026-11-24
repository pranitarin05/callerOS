import * as React from "react";

export function Table({ className, ...props }: React.TableHTMLAttributes<HTMLTableElement>) {
  return (
    <div className="overflow-x-auto">
      <table className={`w-full border-collapse text-left ${className || ""}`} {...props} />
    </div>
  );
}

export function TableHeader(props: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead
      className="border-b border-[#27272a] bg-[#121215] text-[11px] font-medium uppercase tracking-[0.04em] text-[#a1a1aa]"
      {...props}
    />
  );
}

export function TableBody(props: React.HTMLAttributes<HTMLTableSectionElement>) {
  return <tbody className="divide-y divide-[#1f1f23]" {...props} />;
}

export function TableRow(props: React.HTMLAttributes<HTMLTableRowElement>) {
  return <tr className="transition-colors hover:bg-[#18181b]" {...props} />;
}

export function TableCell(props: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return <td className="px-4 py-3 text-sm text-[#e3e1ec]" {...props} />;
}
