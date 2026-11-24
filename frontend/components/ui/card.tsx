import * as React from "react";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-lg border border-[#1f1f23] bg-[#121215] p-6 ${className || ""}`}
      {...props}
    />
  );
}
