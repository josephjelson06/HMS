"use client";

import { format } from "date-fns";
import { CalendarIcon } from "lucide-react";
import type { DateRange } from "react-day-picker";

import { Calendar } from "@/components/ui/primitives/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/primitives/popover";
import { cn } from "@/lib/utils/cn";

export type DateRangeValue = DateRange | undefined;

export interface DateRangePickerProps {
  value: DateRangeValue;
  onChange: (value: DateRangeValue) => void;
  className?: string;
  placeholder?: string;
  numberOfMonths?: number;
}

function renderLabel(value: DateRangeValue, placeholder: string) {
  if (!value?.from) return placeholder;
  if (!value.to) return format(value.from, "PP");
  return `${format(value.from, "PP")} - ${format(value.to, "PP")}`;
}

export function DateRangePicker({
  value,
  onChange,
  className,
  placeholder = "Pick a date range",
  numberOfMonths = 2
}: DateRangePickerProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={cn(
            "ui-input inline-flex items-center justify-between gap-2 text-left font-normal",
            !value?.from && "text-[color:var(--color-text-muted)]",
            className
          )}
        >
          <span>{renderLabel(value, placeholder)}</span>
          <CalendarIcon className="size-4 text-[color:var(--color-text-muted)]" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0">
        <Calendar
          initialFocus
          mode="range"
          selected={value}
          onSelect={onChange}
          numberOfMonths={numberOfMonths}
        />
      </PopoverContent>
    </Popover>
  );
}
