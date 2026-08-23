"use client";

import * as React from "react";
import { HelpCircle } from "lucide-react";

interface TooltipProps {
  content: string;
  children?: React.ReactNode;
}

export function Tooltip({ content, children }: TooltipProps) {
  const [show, setShow] = React.useState(false);

  return (
    <div className="relative inline-block">
      <button
        type="button"
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        onClick={() => setShow(!show)}
        className="inline-flex items-center text-muted-foreground hover:text-foreground transition-colors"
      >
        {children || <HelpCircle className="h-4 w-4" />}
      </button>
      {show && (
        <div className="absolute z-50 w-64 p-3 text-sm bg-popover text-popover-foreground border border-border rounded-lg shadow-lg bottom-full left-1/2 transform -translate-x-1/2 mb-2">
          {content}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
            <div className="border-4 border-transparent border-t-popover"></div>
          </div>
        </div>
      )}
    </div>
  );
}
