import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, Info, CheckCircle } from "lucide-react";
import type { Explanation } from "@/lib/explanations";

interface ExplanationCardProps {
  explanation: Explanation;
  showIcon?: boolean;
}

export function ExplanationCard({ explanation, showIcon = true }: ExplanationCardProps) {
  const urgencyColors = {
    critical: "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800",
    high: "bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800",
    medium: "bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800",
    low: "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800",
  };

  const urgencyIcons = {
    critical: <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />,
    high: <AlertCircle className="h-5 w-5 text-orange-600 dark:text-orange-400" />,
    medium: <Info className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />,
    low: <CheckCircle className="h-5 w-5 text-blue-600 dark:text-blue-400" />,
  };

  return (
    <Card className={urgencyColors[explanation.urgency]}>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2 text-lg">
          {showIcon && urgencyIcons[explanation.urgency]}
          <span>{explanation.title}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="font-semibold text-gray-900 dark:text-white mb-1">{explanation.simple}</p>
        </div>

        <div>
          <h4 className="font-semibold text-gray-900 dark:text-white mb-1">What does this mean?</h4>
          <p className="text-gray-700 dark:text-gray-300 text-sm">{explanation.whatItMeans}</p>
        </div>

        <div>
          <h4 className="font-semibold text-gray-900 dark:text-white mb-1">What should you do?</h4>
          <p className="text-gray-700 dark:text-gray-300 text-sm">{explanation.whatToDo}</p>
        </div>
      </CardContent>
    </Card>
  );
}
