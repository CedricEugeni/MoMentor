import { useEffect, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { LayoutDashboard, List, TrendingUp, Settings as SettingsIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { hasPendingRuns } from "@/lib/api";
import { useCurrencyPreference } from "@/lib/currency";
import { cn } from "@/lib/utils";

export default function Layout() {
  const location = useLocation();
  const [hasPending, setHasPending] = useState(false);
  const { currency, setCurrency } = useCurrencyPreference();

  const { data } = useQuery({
    queryKey: ["pendingRuns"],
    queryFn: hasPendingRuns,
    refetchInterval: 30000, // Check every 30 seconds
  });

  useEffect(() => {
    if (data) {
      setHasPending(data.has_pending);
    }
  }, [data]);

  const navItems = [
    { path: "/", label: "Dashboard", icon: LayoutDashboard },
    { path: "/runs", label: "Runs & Rebalancing", icon: List, hasBadge: hasPending },
    { path: "/portfolio", label: "Portfolio", icon: TrendingUp },
    { path: "/settings", label: "Settings", icon: SettingsIcon },
  ];

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold">MoMentor</h1>
              <p className="text-sm text-muted-foreground">Momentum Investing Strategy Mentor</p>
            </div>

            <nav className="flex space-x-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;

                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      "relative flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors",
                      isActive ? "bg-primary text-primary-foreground" : "hover:bg-accent hover:text-accent-foreground",
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                    {item.hasBadge && <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-destructive" />}
                  </Link>
                );
              })}
            </nav>

            <div className="flex items-center gap-2">
              <Button variant={currency === "USD" ? "default" : "outline"} size="sm" onClick={() => setCurrency("USD")}>
                USD
              </Button>
              <Button variant={currency === "EUR" ? "default" : "outline"} size="sm" onClick={() => setCurrency("EUR")}>
                EUR
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
