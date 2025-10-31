"use client";

import * as React from "react";
import { ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export function Select({
  value,
  onChange,
  options,
  placeholder = "Select...",
  disabled = false,
  className,
}: SelectProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const selectRef = React.useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (disabled) return;

    switch (event.key) {
      case "Enter":
      case " ":
        event.preventDefault();
        setIsOpen(!isOpen);
        break;
      case "Escape":
        setIsOpen(false);
        break;
      case "ArrowDown":
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          const currentIndex = options.findIndex((opt) => opt.value === value);
          if (currentIndex < options.length - 1) {
            onChange(options[currentIndex + 1].value);
          }
        }
        break;
      case "ArrowUp":
        event.preventDefault();
        if (isOpen) {
          const currentIndex = options.findIndex((opt) => opt.value === value);
          if (currentIndex > 0) {
            onChange(options[currentIndex - 1].value);
          }
        }
        break;
    }
  };

  const selectedOption = options.find((opt) => opt.value === value);
  const displayText = selectedOption ? selectedOption.label : placeholder;

  return (
    <div ref={selectRef} className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        className={cn(
          "w-full flex items-center justify-between px-4 py-2.5 bg-white border border-gray-300 rounded-lg text-sm font-medium text-left shadow-sm transition-all duration-200",
          "hover:bg-gray-50 hover:border-gray-400",
          "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
          disabled && "opacity-50 cursor-not-allowed",
          !disabled && "cursor-pointer",
          !selectedOption && "text-gray-500",
          selectedOption && "text-gray-700"
        )}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className="truncate">{displayText}</span>
        <ChevronDown
          className={cn(
            "h-4 w-4 text-gray-400 transition-transform duration-200 flex-shrink-0 ml-2",
            isOpen && "transform rotate-180"
          )}
        />
      </button>

      {isOpen && !disabled && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-xl overflow-hidden animate-in fade-in-0 zoom-in-95">
          <div className="max-h-60 overflow-y-auto py-1">
            {options.map((option) => {
              const isSelected = option.value === value;
              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => {
                    onChange(option.value);
                    setIsOpen(false);
                  }}
                  className={cn(
                    "w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium text-left transition-colors",
                    isSelected
                      ? "bg-blue-50 text-blue-700"
                      : "text-gray-700 hover:bg-gray-100"
                  )}
                  role="option"
                  aria-selected={isSelected}
                >
                  <span>{option.label}</span>
                  {isSelected && (
                    <Check className="h-4 w-4 text-blue-700 flex-shrink-0 ml-2" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
