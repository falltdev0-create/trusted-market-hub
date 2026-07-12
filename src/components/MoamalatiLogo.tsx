type Props = {
  variant?: "full" | "icon";
  size?: number;
  className?: string;
  showTagline?: boolean;
};

export function MoamalatiLogo({ variant = "full", size = 36, className = "", showTagline = false }: Props) {
  const icon = (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <defs>
        <linearGradient id="mlGrad" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#1B4F72" />
          <stop offset="100%" stopColor="#2E86C1" />
        </linearGradient>
      </defs>
      <path
        d="M24 2L42 8V24C42 34 34 42 24 46C14 42 6 34 6 24V8L24 2Z"
        fill="url(#mlGrad)"
      />
      <text
        x="24"
        y="30"
        textAnchor="middle"
        fontSize="22"
        fontWeight="800"
        fill="#fff"
        fontFamily="Cairo, sans-serif"
      >
        م
      </text>
      <path
        d="M16 34L21 39L34 26"
        stroke="#F39C12"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
        opacity="0.95"
      />
    </svg>
  );

  if (variant === "icon") return <span className={className}>{icon}</span>;

  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      {icon}
      <span className="flex flex-col leading-tight">
        <span className="text-xl font-extrabold text-primary">مسكن</span>
        {showTagline && (
          <span className="text-[11px] text-muted-foreground">ثق، تعامل، اطمئن</span>
        )}
      </span>
    </span>
  );
}
