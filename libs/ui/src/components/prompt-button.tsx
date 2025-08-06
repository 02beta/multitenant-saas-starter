"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Brain, ChevronDown, Heart, Layout, Sparkles, Zap } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@workspace/ui/components/ui/dropdown-menu";
import { toast } from "sonner";

interface Option {
  id: string;
  icon: React.ReactNode;
  label: string;
  description: string;
}

const options: Option[] = [
  {
    id: "basic",
    icon: <Sparkles className="w-4 h-4" />,
    label: "Basic",
    description: "Standard prompt for AI code editors",
  },
  {
    id: "extended",
    icon: <Brain className="w-4 h-4" />,
    label: "Extended",
    description: "Extended prompt for complex components",
  },
  {
    id: "lovable",
    icon: <Heart className="w-4 h-4" />,
    label: "Lovable",
    description: "Optimized for Lovable.dev",
  },
  {
    id: "bolt",
    icon: <Zap className="w-4 h-4" />,
    label: "Bolt.new",
    description: "Optimized for Bolt.new",
  },
  {
    id: "sitebrew",
    icon: <Layout className="w-4 h-4" />,
    label: "sitebrew.ai",
    description: "Optimized for sitebrew.ai",
  },
];

export function SplitButtonDropdown() {
  const [selectedOption, setSelectedOption] = React.useState<Option>(
    options[0] ?? { id: "", icon: <></>, label: "", description: "" }
  );
  const [isOpen, setIsOpen] = React.useState(false);
  const handleMainButtonClick = () => {
    return toast("Main button clicked.", {
      description: "option:" + JSON.stringify(selectedOption.label),
    });
  };

  return (
    <div className="flex items-center justify-center p-4">
      <div className="flex rounded-md shadow-sm">
        {/* Main Button */}
        <button
          onClick={handleMainButtonClick}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium
            bg-white border border-r-0 rounded-l-md hover:bg-gray-50
            dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700"
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={selectedOption.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
            >
              {selectedOption.icon}
            </motion.div>
          </AnimatePresence>
          <span className="hidden sm:inline-block">{selectedOption.label}</span>
        </button>

        {/* Dropdown Trigger */}
        <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
          <DropdownMenuTrigger asChild>
            <button
              className="px-3 py-2 text-sm font-medium bg-white border rounded-r-md
                hover:bg-gray-50 focus:outline-none
                focus:ring-offset-2 border-l-gray-200
                dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700"
            >
              <ChevronDown
                className={`w-4 h-4 transition-transform duration-200 ${
                  isOpen ? "rotate-180" : ""
                }`}
              />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-[200px] sm:w-[250px]">
            {options.map((option, index) => (
              <React.Fragment key={option.id}>
                {index === 2 && <DropdownMenuSeparator />}
                <DropdownMenuItem
                  className="flex items-start gap-2 p-3 cursor-pointer"
                  onClick={() => setSelectedOption(option)}
                >
                  <div className="flex-shrink-0 mt-1">{option.icon}</div>
                  <div className="flex flex-col">
                    <span className="font-medium">{option.label}</span>
                    <span className="text-xs text-muted-foreground">
                      {option.description}
                    </span>
                  </div>
                </DropdownMenuItem>
              </React.Fragment>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
