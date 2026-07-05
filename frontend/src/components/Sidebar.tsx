import Link from "next/link";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard" },
  { href: "/stock", label: "Stock Workspace" },
  { href: "/portfolio", label: "Portfolio" },
];

export default function Sidebar() {
  return (
    <aside className="w-56 border-r border-gray-200 dark:border-gray-800 p-4 flex flex-col gap-2">
      <h1 className="text-lg font-bold mb-4">AI Investment OS</h1>
      {NAV_ITEMS.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className="px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          {item.label}
        </Link>
      ))}
    </aside>
  );
}
