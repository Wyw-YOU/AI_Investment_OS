import Sidebar from "@/components/Sidebar";
import HotStocks from "@/components/HotStocks";
import AlertList from "@/components/AlertList";
import AnalyzePanel from "@/components/AnalyzePanel";
import NotificationBell from "@/components/NotificationBell";

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6 space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <NotificationBell />
        </header>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AnalyzePanel />
          <HotStocks />
        </div>
        <AlertList />
      </main>
    </div>
  );
}
