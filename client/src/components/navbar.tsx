import { CircleHelp } from "lucide-react";

interface NavbarProps {
  onHelpClick: () => void;
}

export function Navbar({ onHelpClick }: NavbarProps) {
  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center">
              <svg
                className="h-6 w-6 text-primary mr-2"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"
                />
              </svg>
              <span className="font-semibold text-xl text-gray-800">
                TranslatePDF
              </span>
            </div>
          </div>
          <div className="flex items-center">
            <button
              type="button"
              onClick={onHelpClick}
              className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-primary hover:text-primary-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <CircleHelp className="mr-1 h-4 w-4" />
              Help
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
