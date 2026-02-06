"use client";

import type { ReactNode } from "react";

import { AppFrame } from "@/components/layout/primitives/app-frame";
import { PageContainer } from "@/components/layout/primitives/page-container";
import { Navbar } from "@/components/layout/navbar";
import { UserTypeGuard } from "@/components/features/auth/permission-guard";

export default function HotelLayout({ children }: { children: ReactNode }) {
  return (
    <UserTypeGuard userType="hotel">
      <AppFrame variant="hotel">
        <div className="min-w-0">
          <Navbar />
          <main className="p-6 pt-4">
            <PageContainer>{children}</PageContainer>
          </main>
        </div>
      </AppFrame>
    </UserTypeGuard>
  );
}
