import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { generateRun, getCurrentPortfolio } from "@/lib/api";
import { formatCurrency, formatPercent, formatDate } from "@/lib/utils";
import { Rocket, TrendingUp, TrendingDown } from "lucide-react";

export default function Dashboard() {
  const [capital, setCapital] = useState("");
  const [testMode, setTestMode] = useState(false);
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Check if portfolio exists
  const { data: portfolio, isLoading: isLoadingPortfolio } = useQuery({
    queryKey: ["portfolio"],
    queryFn: getCurrentPortfolio,
    refetchInterval: 60000, // Refresh every minute
  });

  const generateMutation = useMutation({
    mutationFn: (data: { mode: string; capital?: number }) => generateRun(data.mode, data.capital),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["runs"] });
      queryClient.invalidateQueries({ queryKey: ["pendingRuns"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      setShowGenerateDialog(false);
      navigate(`/runs/${data.run_id}`);
    },
  });

  const handleGenerate = () => {
    const capitalValue = capital ? parseFloat(capital) : undefined;
    const mode = testMode ? "test" : "manual";
    generateMutation.mutate({ mode, capital: capitalValue });
  };

  if (isLoadingPortfolio) {
    return <div>Loading...</div>;
  }

  // If portfolio exists, show portfolio dashboard
  if (portfolio?.has_portfolio) {
    const totalPnLPositive = (portfolio.total_pnl_usd || 0) >= 0;

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
            <p className="text-muted-foreground">
              Portfolio overview with P&L since {portfolio.validation_date ? formatDate(portfolio.validation_date) : "last rebalancing"}
            </p>
          </div>
          <Button onClick={() => setShowGenerateDialog(true)} size="lg">
            <Rocket className="mr-2 h-4 w-4" />
            New Rebalancing
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Entry Value</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(portfolio.total_entry_value || 0)}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Current Value</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(portfolio.total_current_value || 0)}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold flex items-center space-x-2 ${totalPnLPositive ? "text-green-600" : "text-red-600"}`}>
                {totalPnLPositive ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
                <span>{formatCurrency(portfolio.total_pnl_usd || 0)}</span>
              </div>
              <p className={`text-sm ${totalPnLPositive ? "text-green-600" : "text-red-600"}`}>{formatPercent(portfolio.total_pnl_percent || 0)}</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Current Positions</CardTitle>
            <CardDescription>Live portfolio tracking</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Shares</TableHead>
                  <TableHead>Entry Price</TableHead>
                  <TableHead>Current Price</TableHead>
                  <TableHead>Current Value</TableHead>
                  <TableHead className="text-right">P&L</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {portfolio.positions?.map((pos) => {
                  const isPositive = pos.pnl_usd >= 0;
                  return (
                    <TableRow key={pos.symbol}>
                      <TableCell className="font-medium">{pos.symbol}</TableCell>
                      <TableCell>{pos.shares}</TableCell>
                      <TableCell>{formatCurrency(pos.entry_price)}</TableCell>
                      <TableCell>{formatCurrency(pos.current_price)}</TableCell>
                      <TableCell>{formatCurrency(pos.current_value)}</TableCell>
                      <TableCell className={`text-right font-medium ${isPositive ? "text-green-600" : "text-red-600"}`}>
                        {formatCurrency(pos.pnl_usd)} ({formatPercent(pos.pnl_percent)})
                      </TableCell>
                    </TableRow>
                  );
                })}
                {(portfolio.uninvested_cash || 0) > 0 && (
                  <TableRow>
                    <TableCell className="font-medium">Cash</TableCell>
                    <TableCell colSpan={3}>Uninvested</TableCell>
                    <TableCell>{formatCurrency(portfolio.uninvested_cash || 0)}</TableCell>
                    <TableCell className="text-right">-</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button className="w-full" onClick={() => navigate("/portfolio")} variant="outline">
              View Full Portfolio Details
            </Button>
            <Button className="w-full" onClick={() => navigate("/runs")} variant="outline">
              View Rebalancing History
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // If no portfolio, show setup form
  return (
    <>
      <div className="max-w-2xl mx-auto space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">Generate momentum-based portfolio recommendations</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Generate Recommendations</CardTitle>
            <CardDescription>Enter your initial capital to get started, or leave empty to use the current portfolio value.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="capital">Initial Capital (USD)</Label>
              <Input id="capital" type="number" placeholder="10000" value={capital} onChange={(e) => setCapital(e.target.value)} min="0" step="100" />
              <p className="text-sm text-muted-foreground">Leave empty to calculate from your current portfolio</p>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="test-mode">Test Mode</Label>
                <p className="text-sm text-muted-foreground">Generate test recommendations (can be run multiple times per week)</p>
              </div>
              <Switch id="test-mode" checked={testMode} onCheckedChange={setTestMode} />
            </div>

            <Button className="w-full" size="lg" onClick={handleGenerate} disabled={generateMutation.isPending}>
              <Rocket className="mr-2 h-4 w-4" />
              {generateMutation.isPending ? "Generating..." : "Generate Recommendations"}
            </Button>

            {generateMutation.isError && <p className="text-sm text-destructive">Error: {(generateMutation.error as Error).message}</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>How It Works</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                1
              </div>
              <div>
                <p className="font-medium">Generate Recommendations</p>
                <p className="text-sm text-muted-foreground">The momentum algorithm analyzes US stocks and provides allocation percentages</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                2
              </div>
              <div>
                <p className="font-medium">Review Optimized Moves</p>
                <p className="text-sm text-muted-foreground">View both cash flow and swap strategies to minimize transactions</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                3
              </div>
              <div>
                <p className="font-medium">Confirm Actual Positions</p>
                <p className="text-sm text-muted-foreground">After executing trades, enter your actual positions to track performance</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Dialog for generating new rebalancing when portfolio exists */}
      <Dialog open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Generate New Rebalancing</DialogTitle>
            <DialogDescription>Create a new momentum-based portfolio recommendation</DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="dialog-capital">Capital (USD)</Label>
              <Input
                id="dialog-capital"
                type="number"
                placeholder="Leave empty for current portfolio value"
                value={capital}
                onChange={(e) => setCapital(e.target.value)}
                min="0"
                step="100"
              />
              <p className="text-sm text-muted-foreground">Leave empty to use current portfolio value</p>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="dialog-test-mode">Test Mode</Label>
                <p className="text-sm text-muted-foreground">Generate test recommendations</p>
              </div>
              <Switch id="dialog-test-mode" checked={testMode} onCheckedChange={setTestMode} />
            </div>

            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowGenerateDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleGenerate} disabled={generateMutation.isPending}>
                {generateMutation.isPending ? "Generating..." : "Generate"}
              </Button>
            </div>

            {generateMutation.isError && <p className="text-sm text-destructive">Error: {(generateMutation.error as Error).message}</p>}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
