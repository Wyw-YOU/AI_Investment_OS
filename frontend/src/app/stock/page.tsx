import Sidebar from "@/components/Sidebar";
import StockWorkspace from "@/components/StockWorkspace";
import NotificationBell from "@/components/NotificationBell";
import StockInput from "@/components/StockInput";

export default function StockPage() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6 space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">个股分析</h1>
          <div className="flex items-center gap-4">
            <StockInput />
            <NotificationBell />
          </div>
        </header>
        <StockWorkspace />
      </main>
    </div>
  );
}
