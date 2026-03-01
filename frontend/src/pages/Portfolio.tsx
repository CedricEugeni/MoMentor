import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getCurrentPortfolio } from "@/lib/api";
import { useCurrencyPreference } from "@/lib/currency";
import { formatCurrency, formatPercent, formatDate, formatShares } from "@/lib/utils";
import { TrendingUp, TrendingDown } from "lucide-react";

export default function Portfolio() {
  const { currency } = useCurrencyPreference();
  const { data: portfolio, isLoading } = useQuery({
    queryKey: ["portfolio"],
    queryFn: getCurrentPortfolio,
    refetchInterval: 60000, // Refresh every minute for live prices
  });

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!portfolio?.has_portfolio) {
    return (
      <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight">Current Portfolio</h2>
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            {portfolio?.message || "No portfolio data available. Generate and confirm your first run to start tracking."}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (portfolio.error) {
    return (
      <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight">Current Portfolio</h2>
        <Card className="border-destructive">
          <CardContent className="py-12 text-center">
            <p className="text-destructive">{portfolio.error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const totalPnLPositive = (portfolio.total_pnl_usd || 0) >= 0;
  const fxRate = portfolio.fx_rate_to_usd || 1;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Current Portfolio</h2>
        <p className="text-muted-foreground">
          Live portfolio value with P&L since {portfolio.validation_date ? formatDate(portfolio.validation_date) : "last rebalancing"}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Entry Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(portfolio.total_entry_value || 0, { currency, fxRateToUsd: fxRate })}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Current Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(portfolio.total_current_value || 0, { currency, fxRateToUsd: fxRate })}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold flex items-center space-x-2 ${totalPnLPositive ? "text-green-600" : "text-red-600"}`}>
              {totalPnLPositive ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
              <span>{formatCurrency(portfolio.total_pnl_usd || 0, { currency, fxRateToUsd: fxRate })}</span>
            </div>
            <p className={`text-sm ${totalPnLPositive ? "text-green-600" : "text-red-600"}`}>{formatPercent(portfolio.total_pnl_percent || 0)}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Positions</CardTitle>
          <CardDescription>Current holdings with live prices and P&L</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Symbol</TableHead>
                <TableHead>Shares</TableHead>
                <TableHead>Entry Price</TableHead>
                <TableHead>Current Price</TableHead>
                <TableHead>Entry Value</TableHead>
                <TableHead>Current Value</TableHead>
                <TableHead className="text-right">P&L ({currency})</TableHead>
                <TableHead className="text-right">P&L (%)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {portfolio.positions?.map((pos) => {
                const isPositive = pos.pnl_usd >= 0;
                return (
                  <TableRow key={pos.symbol}>
                    <TableCell className="font-medium">{pos.symbol}</TableCell>
                    <TableCell>{formatShares(pos.shares)}</TableCell>
                    <TableCell>{formatCurrency(pos.entry_price, { currency, fxRateToUsd: fxRate })}</TableCell>
                    <TableCell>{formatCurrency(pos.current_price, { currency, fxRateToUsd: fxRate })}</TableCell>
                    <TableCell>{formatCurrency(pos.entry_value, { currency, fxRateToUsd: fxRate })}</TableCell>
                    <TableCell>{formatCurrency(pos.current_value, { currency, fxRateToUsd: fxRate })}</TableCell>
                    <TableCell className={`text-right font-medium ${isPositive ? "text-green-600" : "text-red-600"}`}>
                      {formatCurrency(pos.pnl_usd, { currency, fxRateToUsd: fxRate })}
                    </TableCell>
                    <TableCell className={`text-right ${isPositive ? "text-green-600" : "text-red-600"}`}>{formatPercent(pos.pnl_percent)}</TableCell>
                  </TableRow>
                );
              })}
              {(portfolio.uninvested_cash || 0) > 0 && (
                <TableRow>
                  <TableCell className="font-medium">Cash</TableCell>
                  <TableCell colSpan={4}>Uninvested</TableCell>
                  <TableCell>{formatCurrency(portfolio.uninvested_cash || 0, { currency, fxRateToUsd: fxRate })}</TableCell>
                  <TableCell className="text-right">-</TableCell>
                  <TableCell className="text-right">-</TableCell>
                </TableRow>
              )}
              <TableRow className="font-bold bg-muted/50">
                <TableCell>Total</TableCell>
                <TableCell colSpan={4}></TableCell>
                <TableCell>{formatCurrency(portfolio.total_current_value || 0, { currency, fxRateToUsd: fxRate })}</TableCell>
                <TableCell className={`text-right ${totalPnLPositive ? "text-green-600" : "text-red-600"}`}>
                  {formatCurrency(portfolio.total_pnl_usd || 0, { currency, fxRateToUsd: fxRate })}
                </TableCell>
                <TableCell className={`text-right ${totalPnLPositive ? "text-green-600" : "text-red-600"}`}>
                  {formatPercent(portfolio.total_pnl_percent || 0)}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
