import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { getRunDetails, confirmPositions } from "@/lib/api";
import { getPendingConfirmation, savePendingConfirmation, removePendingConfirmation } from "@/lib/localStorage";
import { formatCurrency, formatDate } from "@/lib/utils";
import { ArrowDown, ArrowUp, ArrowRight, AlertTriangle } from "lucide-react";

export default function RunDetails() {
  const { runId } = useParams();
  const queryClient = useQueryClient();
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [positions, setPositions] = useState<Record<string, { shares: string; price: string }>>({});
  const [uninvestedCash, setUninvestedCash] = useState("");
  const [warningData, setWarningData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [marketDataUnavailable, setMarketDataUnavailable] = useState(false);

  const { data: run, isLoading } = useQuery({
    queryKey: ["run", runId],
    queryFn: () => getRunDetails(Number(runId)),
    enabled: !!runId,
  });

  // Load pending confirmation from localStorage
  useEffect(() => {
    if (run && run.status === "pending") {
      const pending = getPendingConfirmation(run.id);
      if (pending) {
        const posMap: Record<string, { shares: string; price: string }> = {};
        pending.positions?.forEach((p) => {
          if (p && p.symbol && p.shares != null && p.avg_price != null) {
            posMap[p.symbol] = { shares: p.shares.toString(), price: p.avg_price.toString() };
          }
        });
        setPositions(posMap);
        setUninvestedCash(pending.uninvestedCash != null ? pending.uninvestedCash.toString() : "0");
        setError("Market data was unavailable during your last attempt. Please try again.");
        setMarketDataUnavailable(true);
      }
    }
  }, [run]);

  const confirmMutation = useMutation({
    mutationFn: (data: { positions: any[]; cash: number; force: boolean }) => confirmPositions(Number(runId), data.positions, data.cash, data.force),
    onSuccess: (response) => {
      if (response.warning) {
        setWarningData(response);
      } else {
        // Success
        removePendingConfirmation(run!.id);
        queryClient.invalidateQueries({ queryKey: ["run", runId] });
        queryClient.invalidateQueries({ queryKey: ["runs"] });
        queryClient.invalidateQueries({ queryKey: ["pendingRuns"] });
        queryClient.invalidateQueries({ queryKey: ["portfolio"] });
        setShowConfirmDialog(false);
        setWarningData(null);
        setError(null);
        setMarketDataUnavailable(false);
      }
    },
    onError: (error: any) => {
      // Handle market data unavailable (503) or other errors
      const posArray = Object.entries(positions).map(([symbol, data]) => ({
        symbol,
        shares: parseInt(data.shares),
        avg_price: parseFloat(data.price),
      }));
      savePendingConfirmation(run!.id, posArray, parseFloat(uninvestedCash));

      const isMarketDataUnavailable = error?.response?.data?.detail?.error === "MARKET_DATA_UNAVAILABLE";
      const errorMessage =
        error?.response?.data?.detail?.message || error?.response?.data?.message || error?.message || "An error occurred while confirming positions";
      setError(errorMessage);
      setMarketDataUnavailable(isMarketDataUnavailable);
    },
  });

  const handleConfirm = (force = false) => {
    const posArray = Object.entries(positions)
      .filter(([_, data]) => data.shares && data.price)
      .map(([symbol, data]) => ({
        symbol,
        shares: parseInt(data.shares),
        avg_price: parseFloat(data.price),
      }));

    confirmMutation.mutate({
      positions: posArray,
      cash: parseFloat(uninvestedCash) || 0,
      force,
    });
  };

  if (isLoading || !run) {
    return <div>Loading...</div>;
  }

  const initializePositions = () => {
    const posMap: Record<string, { shares: string; price: string }> = {};
    run.recommendations.forEach((rec) => {
      posMap[rec.symbol] = { shares: "", price: "" };
    });
    setPositions(posMap);
    setShowConfirmDialog(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Run Details</h2>
          <p className="text-muted-foreground">{formatDate(run.run_date)}</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge>{run.trigger_type.toUpperCase()}</Badge>
          <Badge variant={run.status === "completed" ? "default" : "outline"}>{run.status.toUpperCase()}</Badge>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Total Capital</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(run.total_capital_usd)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Uninvested Cash</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(run.uninvested_cash_usd)}</div>
          </CardContent>
        </Card>
      </div>

      {run.status === "pending" && (
        <Card className="border-orange-500">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              <span>Action Required</span>
            </CardTitle>
            <CardDescription>After executing the recommended moves, confirm your actual positions to track performance.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={initializePositions}>Confirm Positions</Button>
            {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="recommendations">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          <TabsTrigger value="cashflow">Cash Flow Moves</TabsTrigger>
          <TabsTrigger value="swaps">Swap Moves</TabsTrigger>
          {run.actual_positions && <TabsTrigger value="actual">Actual Positions</TabsTrigger>}
        </TabsList>

        <TabsContent value="recommendations">
          <Card>
            <CardHeader>
              <CardTitle>Recommended Allocations</CardTitle>
              <CardDescription>Target portfolio allocation percentages</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Percentage</TableHead>
                    <TableHead className="text-right">Amount (USD)</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {run.recommendations && run.recommendations.length > 0 ? (
                    run.recommendations.map((rec) => (
                      <TableRow key={rec.symbol}>
                        <TableCell className="font-medium">{rec.symbol}</TableCell>
                        <TableCell>{(rec.target_percentage * 100).toFixed(2)}%</TableCell>
                        <TableCell className="text-right">{formatCurrency(rec.target_amount_usd)}</TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center text-muted-foreground">
                        No recommendations available
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cashflow">
          <Card>
            <CardHeader>
              <CardTitle>Cash Flow Moves</CardTitle>
              <CardDescription>Sell positions first (to free cash), then buy new positions</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Order</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Shares</TableHead>
                    <TableHead className="text-right">Value (USD)</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {run.cashflow_moves && run.cashflow_moves.length > 0 ? (
                    run.cashflow_moves.map((move) => (
                      <TableRow key={move.order_index}>
                        <TableCell>{move.order_index}</TableCell>
                        <TableCell>
                          <Badge variant={move.action === "SELL" ? "destructive" : "default"}>
                            {move.action === "SELL" ? (
                              <>
                                <ArrowDown className="mr-1 h-3 w-3" /> SELL
                              </>
                            ) : (
                              <>
                                <ArrowUp className="mr-1 h-3 w-3" /> BUY
                              </>
                            )}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-medium">{move.symbol}</TableCell>
                        <TableCell>{move.suggested_shares}</TableCell>
                        <TableCell className="text-right">{formatCurrency(move.suggested_value_usd)}</TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-muted-foreground">
                        No cashflow moves available
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="swaps">
          <Card>
            <CardHeader>
              <CardTitle>Swap Moves</CardTitle>
              <CardDescription>Direct swaps to minimize number of transactions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {run.swap_moves && run.swap_moves.length > 0 ? (
                  run.swap_moves.map((move) => (
                    <div key={move.order_index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center space-x-4">
                        <Badge variant="outline">{move.order_index}</Badge>
                        <div className="flex items-center space-x-2">
                          {move.from_symbol && (
                            <>
                              <span className="font-medium">
                                Vendre {move.swap_shares_from} {move.from_symbol}
                              </span>
                              <ArrowRight className="h-4 w-4" />
                            </>
                          )}
                          {move.to_symbol && (
                            <span className="font-medium">
                              Acheter {move.swap_shares_to} {move.to_symbol}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium">{formatCurrency(move.swap_value_usd)}</div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-center text-muted-foreground py-4">No swap moves available</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {run.actual_positions && (
          <TabsContent value="actual">
            <Card>
              <CardHeader>
                <CardTitle>Actual Positions</CardTitle>
                <CardDescription>Positions confirmed by user</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Symbol</TableHead>
                      <TableHead>Shares</TableHead>
                      <TableHead>Avg Price</TableHead>
                      <TableHead className="text-right">Total Value</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {run.actual_positions.map((pos) => (
                      <TableRow key={pos.symbol}>
                        <TableCell className="font-medium">{pos.symbol}</TableCell>
                        <TableCell>{pos.actual_shares}</TableCell>
                        <TableCell>{formatCurrency(pos.actual_avg_price_usd)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(pos.total_value_usd)}</TableCell>
                      </TableRow>
                    ))}
                    {run.actual_cash !== null && (
                      <TableRow>
                        <TableCell className="font-medium">Cash</TableCell>
                        <TableCell colSpan={2}>Uninvested</TableCell>
                        <TableCell className="text-right">{formatCurrency(run.actual_cash)}</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>

      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Confirm Actual Positions</DialogTitle>
            <DialogDescription>Enter the actual number of shares and average price you paid for each position</DialogDescription>
          </DialogHeader>

          <div className="rounded-lg border bg-muted/40 p-4 text-sm">
            <p className="font-medium">Recommended allocations</p>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {run.recommendations.map((rec) => (
                <div key={rec.symbol} className="flex items-center justify-between">
                  <span className="font-medium">{rec.symbol}</span>
                  <span className="text-muted-foreground">
                    {(rec.target_percentage * 100).toFixed(2)}% ({formatCurrency(rec.target_amount_usd)})
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            {Object.keys(positions).map((symbol) => (
              <div key={symbol} className="grid grid-cols-3 gap-4 items-end">
                <div>
                  <Label className="font-bold">{symbol}</Label>
                </div>
                <div>
                  <Label htmlFor={`${symbol}-shares`}>Shares</Label>
                  <Input
                    id={`${symbol}-shares`}
                    type="number"
                    value={positions[symbol]?.shares || ""}
                    onChange={(e) =>
                      setPositions({
                        ...positions,
                        [symbol]: { ...positions[symbol], shares: e.target.value },
                      })
                    }
                    placeholder="0"
                  />
                </div>
                <div>
                  <Label htmlFor={`${symbol}-price`}>Avg Price (USD)</Label>
                  <Input
                    id={`${symbol}-price`}
                    type="number"
                    step="0.01"
                    value={positions[symbol]?.price || ""}
                    onChange={(e) =>
                      setPositions({
                        ...positions,
                        [symbol]: { ...positions[symbol], price: e.target.value },
                      })
                    }
                    placeholder="0.00"
                  />
                </div>
              </div>
            ))}

            <div className="pt-4 border-t">
              <Label htmlFor="cash">Uninvested Cash (USD)</Label>
              <Input
                id="cash"
                type="number"
                step="0.01"
                value={uninvestedCash}
                onChange={(e) => setUninvestedCash(e.target.value)}
                placeholder="0.00"
              />
            </div>

            {warningData && (
              <div className="p-4 border-2 border-orange-500 rounded-lg space-y-2">
                <p className="font-medium text-orange-600">
                  {warningData.code === "MARKET_DATA_UNAVAILABLE" ? "Market data unavailable" : "Warning: Value Discrepancy"}
                </p>
                <p className="text-sm">{warningData.message}</p>
                <div className="flex space-x-4 pt-2">
                  <Button variant="outline" onClick={() => setWarningData(null)}>
                    Cancel
                  </Button>
                  <Button variant="destructive" onClick={() => handleConfirm(true)}>
                    Confirm Anyway
                  </Button>
                </div>
              </div>
            )}

            {!warningData && marketDataUnavailable && (
              <div className="p-4 border-2 border-orange-500 rounded-lg space-y-2">
                <p className="font-medium text-orange-600">Market data unavailable</p>
                <p className="text-sm">
                  Yahoo Finance is rate-limiting requests right now. You can confirm anyway and we will use your entered prices.
                </p>
                <div className="flex space-x-4 pt-2">
                  <Button variant="outline" onClick={() => setMarketDataUnavailable(false)}>
                    Cancel
                  </Button>
                  <Button variant="destructive" onClick={() => handleConfirm(true)}>
                    Confirm Anyway
                  </Button>
                </div>
              </div>
            )}

            {!warningData && !marketDataUnavailable && (
              <div className="flex justify-end space-x-2 pt-4">
                <Button variant="outline" onClick={() => setShowConfirmDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={() => handleConfirm(false)} disabled={confirmMutation.isPending}>
                  {confirmMutation.isPending ? "Confirming..." : "Confirm Positions"}
                </Button>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
