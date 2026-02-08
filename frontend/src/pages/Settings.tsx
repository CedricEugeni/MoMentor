import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { resetDatabase } from "@/lib/api";
import { clearAllPendingConfirmations } from "@/lib/localStorage";
import { applyTheme, getThemePreference, setThemePreference, ThemePreference } from "@/lib/theme";
import { AlertTriangle } from "lucide-react";

export default function Settings() {
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [themePreference, setThemePreferenceState] = useState<ThemePreference>("system");

  useEffect(() => {
    const current = getThemePreference();
    setThemePreferenceState(current);
    applyTheme(current);
  }, []);

  const resetMutation = useMutation({
    mutationFn: resetDatabase,
    onSuccess: () => {
      // Clear all localStorage data
      clearAllPendingConfirmations();
      setShowResetDialog(false);
      window.location.reload();
    },
  });

  const handleThemeChange = (value: ThemePreference) => {
    setThemePreferenceState(value);
    setThemePreference(value);
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">Manage application settings and data</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Choose how the app looks on your device</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <Button variant={themePreference === "light" ? "default" : "outline"} onClick={() => handleThemeChange("light")}>
              Light
            </Button>
            <Button variant={themePreference === "dark" ? "default" : "outline"} onClick={() => handleThemeChange("dark")}>
              Dark
            </Button>
            <Button variant={themePreference === "system" ? "default" : "outline"} onClick={() => handleThemeChange("system")}>
              Auto (System)
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">Auto follows your system theme.</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>About MoMentor</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-muted-foreground">
            <strong>MoMentor</strong> is a momentum investing strategy mentor that helps you manage your US stock portfolio using a momentum-based
            allocation algorithm.
          </p>
          <div className="pt-4 space-y-1 text-sm">
            <p>
              <strong>Version:</strong> 1.0.0
            </p>
            <p>
              <strong>Market Data:</strong> Yahoo Finance (Free, 15min delayed)
            </p>
            <p>
              <strong>Currency:</strong> USD only
            </p>
            <p>
              <strong>Auto-Scheduling:</strong> Enabled (11:00 Paris Time, 1st of each month)
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Market Data Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <strong>Source:</strong> Yahoo Finance API (free tier)
          </p>
          <p>
            <strong>Limitations:</strong>
          </p>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-4">
            <li>Maximum 2,000 requests per hour</li>
            <li>Price data delayed by 15 minutes</li>
            <li>Prices updated when you view portfolio or confirm positions</li>
          </ul>
          <p className="text-muted-foreground pt-2">
            These limitations are sufficient for monthly rebalancing strategies and daily portfolio monitoring.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Usage Tips</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div>
            <p className="font-medium">1. Monthly Workflow</p>
            <p className="text-muted-foreground">
              On the 1st of each month at 11:00 (Paris time), the algorithm automatically generates new recommendations. Review them and execute
              trades, then confirm your actual positions.
            </p>
          </div>
          <div>
            <p className="font-medium">2. Test Mode</p>
            <p className="text-muted-foreground">
              Use test mode to generate recommendations multiple times for testing purposes. Test runs are clearly labeled and won't interfere with
              your regular monthly runs.
            </p>
          </div>
          <div>
            <p className="font-medium">3. Position Confirmation</p>
            <p className="text-muted-foreground">
              Always confirm your actual positions after executing trades. This allows the system to: track your real performance, calculate accurate
              P&L, and use your actual capital for the next run.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Danger Zone</CardTitle>
          <CardDescription>Irreversible actions</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-medium mb-2">Reset All Data</h3>
            <p className="text-sm text-muted-foreground mb-4">
              This will permanently delete all algorithm runs, positions, and portfolio data. This action cannot be undone.
            </p>
            <Button variant="destructive" onClick={() => setShowResetDialog(true)}>
              <AlertTriangle className="mr-2 h-4 w-4" />
              Reset Database
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog open={showResetDialog} onOpenChange={setShowResetDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reset All Data?</DialogTitle>
            <DialogDescription>This will permanently delete all your data including:</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <ul className="list-disc list-inside space-y-1 text-sm">
              <li>All algorithm runs (past and pending)</li>
              <li>All confirmed positions</li>
              <li>Portfolio history and performance data</li>
              <li>Cached price data</li>
            </ul>
            <div className="flex justify-end space-x-2 pt-4">
              <Button variant="outline" onClick={() => setShowResetDialog(false)} disabled={resetMutation.isPending}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={() => resetMutation.mutate()} disabled={resetMutation.isPending}>
                {resetMutation.isPending ? "Resetting..." : "Yes, Reset Everything"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
