import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, Info, CheckCircle } from "lucide-react";
import type { Explanation } from "@/lib/explanations";

interface ExplanationCardProps {
  explanation: Explanation;
  showIcon?: boolean;
}

export function ExplanationCard({ explanation, showIcon = true }: ExplanationCardProps) {
  const urgencyColors = {
    critical: "bg-red-50 border-red-200",
    high: "bg-orange-50 border-orange-200",
    medium: "bg-yellow-50 border-yellow-200",
    low: "bg-blue-50 border-blue-200",
  };

  const urgencyIcons = {
    critical: <AlertCircle className="h-5 w-5 text-red-600" />,
    high: <AlertCircle className="h-5 w-5 text-orange-600" />,
    medium: <Info className="h-5 w-5 text-yellow-600" />,
    low: <CheckCircle className="h-5 w-5 text-blue-600" />,
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
          <p className="font-semibold text-gray-900 mb-1">{explanation.simple}</p>
        </div>

        <div>
          <h4 className="font-semibold text-gray-900 mb-1">What does this mean?</h4>
          <p className="text-gray-700 text-sm">{explanation.whatItMeans}</p>
        </div>

        <div>
          <h4 className="font-semibold text-gray-900 mb-1">What should you do?</h4>
          <p className="text-gray-700 text-sm">{explanation.whatToDo}</p>
        </div>
      </CardContent>
    </Card>
  );
}
