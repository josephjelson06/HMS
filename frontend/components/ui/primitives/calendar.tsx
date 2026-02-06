"use client";

import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp } from "lucide-react";
import { DayPicker } from "react-day-picker";

import { cn } from "@/lib/utils/cn";
import "react-day-picker/dist/style.css";

export type CalendarProps = React.ComponentProps<typeof DayPicker>;

export function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  ...props
}: CalendarProps) {
  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      className={cn("p-3", className)}
      classNames={{
        months: "flex flex-col gap-3 sm:flex-row sm:gap-4",
        month: "space-y-2",
        caption: "relative flex items-center justify-center pt-1",
        caption_label: "text-sm font-semibold",
        nav: "flex items-center gap-1",
        nav_button: cn(
          "inline-flex size-7 items-center justify-center rounded-md border border-white/10 bg-white/5 ui-anim",
          "hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--color-accent)]"
        ),
        nav_button_previous: "absolute left-1",
        nav_button_next: "absolute right-1",
        table: "w-full border-collapse space-y-1",
        head_row: "flex",
        head_cell: "w-9 rounded-md text-[0.72rem] font-medium text-[color:var(--color-text-muted)]",
        row: "mt-2 flex w-full",
        cell: "relative h-9 w-9 p-0 text-center text-sm",
        day: cn(
          "inline-flex size-9 items-center justify-center rounded-md ui-anim",
          "hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--color-accent)]"
        ),
        day_selected: "bg-[color:var(--color-accent)] text-black hover:bg-[color:var(--color-accent)]",
        day_today: "border border-[color:var(--color-accent)]",
        day_outside: "text-[color:var(--color-text-muted)] opacity-50",
        day_disabled: "opacity-40",
        day_range_middle: "rounded-none bg-white/10",
        day_range_start: "rounded-l-md bg-[color:var(--color-accent)] text-black",
        day_range_end: "rounded-r-md bg-[color:var(--color-accent)] text-black",
        ...classNames
      }}
      components={{
        Chevron: ({ orientation, className: iconClassName }) => {
          if (orientation === "left") return <ChevronLeft className={cn("size-4", iconClassName)} />;
          if (orientation === "right") return <ChevronRight className={cn("size-4", iconClassName)} />;
          if (orientation === "up") return <ChevronUp className={cn("size-4", iconClassName)} />;
          return <ChevronDown className={cn("size-4", iconClassName)} />;
        }
      }}
      {...props}
    />
  );
}
