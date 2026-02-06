import type { ReactNode } from "react";

import "../styles/globals.css";
import { Providers } from "./providers";

export const metadata = {
  title: "HMS",
  description: "Hotel Management System"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
