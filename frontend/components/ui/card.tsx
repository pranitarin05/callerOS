import { cn } from "@/lib/utils"

export interface CardProps {
  className?: string
}

export function Card({ className, ...props }: CardProps) {
  return (
    <section
      className={cn(
        "rounded-lg border border-border bg-card p-6 shadow-sm",
        className,
      )}
      {...props}
    />
  )
}