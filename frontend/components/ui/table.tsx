import { cn } from "@/lib/utils"

export interface TableHeaderProps {
  className?: string
}

export function TableHeader({ className, ...props }: TableHeaderProps) {
  return (
    <thead className={cn("border-b bg-muted", className)} {...props} />
  )
}

export interface TableRowProps {
  className?: string
}

export function TableRow({ className, ...props }: TableRowProps) {
  return (
    <tr className={cn("hover:bg-muted/50", className)} {...props} />
  )
}

export interface TableCellProps {
  className?: string
}

export function TableCell({ className, ...props }: TableCellProps) {
  return (
    <td className={cn("p-3 text-sm", className)} {...props} />
  )
}

export interface TableBodyProps {
  className?: string
}

export function TableBody({ className, ...props }: TableBodyProps) {
  return (
    <tbody className={cn("divide-y divide-divide-muted", className)} {...props} />
  )
}