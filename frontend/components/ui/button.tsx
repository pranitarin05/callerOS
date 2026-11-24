import * as React from "react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "secondary" | "danger" | "ghost";
};

export function Button({ className, variant = "default", ...props }: ButtonProps) {
  const variants: Record<string, string> = {
    default: "bg-[#fafafa] text-[#09090b] hover:bg-white/90",
    secondary: "bg-[#121215] text-[#ffffff] border border-[#27272a] hover:border-[#3f3f46]",
    danger: "bg-[#93000a] text-[#ffdad6] hover:bg-[#b0000c]",
    ghost: "bg-transparent text-[#a1a1aa] hover:text-white",
  };
  return (
    <button
      className={`inline-flex h-10 items-center justify-center rounded px-4 font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className || ""}`}
      {...props}
    />
  );
}
