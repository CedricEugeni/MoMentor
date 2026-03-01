import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { listRuns } from "@/lib/api";
import { useCurrencyPreference } from "@/lib/currency";
import { formatCurrency, formatDate } from "@/lib/utils";
import { ChevronRight, Clock, CheckCircle2 } from "lucide-react";

export default function Runs() {
  const navigate = useNavigate();
  const { currency } = useCurrencyPreference();
  const { data, isLoading } = useQuery({
    queryKey: ["runs"],
    queryFn: listRuns,
  });

  const getTriggerBadge = (type: string) => {
    const variants = {
      auto: "default",
      manual: "secondary",
      test: "outline",
    } as const;

    return <Badge variant={variants[type as keyof typeof variants]}>{type.toUpperCase()}</Badge>;
  };

  const getStatusIcon = (status: string) => {
    return status === "completed" ? <CheckCircle2 className="h-4 w-4 text-green-600" /> : <Clock className="h-4 w-4 text-orange-600" />;
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Algorithm Runs & Rebalancing</h2>
        <p className="text-muted-foreground">View all algorithm runs and confirm your actual positions</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Runs</CardTitle>
          <CardDescription>Click on a run to view details and confirm positions</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p>Loading...</p>
          ) : !data?.runs || data.runs.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">No algorithm runs yet. Generate your first recommendations from the dashboard.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Capital ({currency})</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.runs.map((run) => (
                  <TableRow key={run.id} className="cursor-pointer hover:bg-muted/50">
                    <TableCell>{formatDate(run.run_date)}</TableCell>
                    <TableCell>{getTriggerBadge(run.trigger_type)}</TableCell>
                    <TableCell>{formatCurrency(run.total_capital_usd, { currency, fxRateToUsd: run.fx_rate_to_usd || 1 })}</TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(run.status)}
                        <span className="capitalize">{run.status}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" onClick={() => navigate(`/runs/${run.id}`)}>
                        View Details
                        <ChevronRight className="ml-2 h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
