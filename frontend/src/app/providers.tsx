"use client";

import { SWRConfig } from "swr";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig
      value={{
        fetcher: (url: string) =>
          fetch(url, {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("token") || ""}`,
            },
          }).then((r) => r.json()),
      }}
    >
      {children}
    </SWRConfig>
  );
}
