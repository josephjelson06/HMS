import type { Invoice } from "@/lib/types/invoices";
import type { Plan } from "@/lib/types/plans";
import type { Subscription } from "@/lib/types/subscriptions";

export interface BillingSummary {
  subscription: Subscription | null;
  plan: Plan | null;
  invoices: Invoice[];
}
