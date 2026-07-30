import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { Bell, LogOut, LayoutGrid, Menu, User, LayoutDashboard, Settings, ListChecks } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth";
import { notificationsApi, tryApi } from "@/lib/api";
import { MoamalatiLogo } from "./MoamalatiLogo";
import { ThemeToggle } from "./ThemeToggle";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";


const NAV_LINKS = [
  { to: "/marketplace", label: "المعرض" },
  { to: "/how-it-works", label: "كيف يعمل" },
  { to: "/", label: "عن المنصة" },
];

export function Navbar() {
  const { user, isLoggedIn, logout } = useAuthStore();
  const navigate = useNavigate();
  const path = useRouterState({ select: (s) => s.location.pathname });

  const { data: unread = 0 } = useQuery<number>({
    queryKey: ["notifications", "unread-count"],
    queryFn: () =>
      tryApi(
        () => notificationsApi.unreadCount().then((r) => r.data?.count ?? r.data?.unread ?? 0),
        2,
      ),
    enabled: isLoggedIn,
    refetchInterval: 30000,
  });

  const isActive = (to: string) => path === to;

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-card/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
        <Link to="/" aria-label="مسكن">
          <MoamalatiLogo />
        </Link>

        <nav className="hidden items-center gap-2 md:flex">
          {NAV_LINKS.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={`relative rounded-md px-4 py-2 text-sm font-semibold transition-colors hover:text-primary ${
                isActive(l.to) ? "text-primary" : "text-foreground"
              }`}
            >
              {l.label}
              {isActive(l.to) && (
                <span className="absolute inset-x-3 -bottom-0.5 h-0.5 rounded-full bg-accent" />
              )}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          {isLoggedIn ? (

            <>
              <Link
                to="/notifications"
                className="relative hidden rounded-full p-2 hover:bg-secondary md:inline-flex"
                aria-label="إشعارات"
              >
                <Bell className="h-5 w-5 text-foreground" />
                {unread > 0 && (
                  <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-bold text-destructive-foreground">
                    {unread > 99 ? "99+" : unread}
                  </span>
                )}
              </Link>
              {(user?.role === "admin" || user?.role === "super_admin" || user?.admin_role) && (
                <Link
                  to="/admin"
                  className="hidden items-center rounded-md bg-accent px-3 py-1.5 text-sm font-semibold text-accent-foreground md:inline-flex"
                >
                  <LayoutGrid className="ms-1 h-4 w-4" /> الإدارة
                </Link>
              )}

              <DropdownMenu>
                <DropdownMenuTrigger className="flex items-center gap-2 rounded-full bg-secondary px-2.5 py-1.5 outline-none hover:bg-secondary/80">
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                    {user?.name?.charAt(0) ?? "U"}
                  </div>
                  <span className="hidden text-sm font-semibold md:inline">{user?.name}</span>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>حسابي</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate({ to: "/dashboard" })}>
                    <LayoutDashboard className="ms-2 h-4 w-4" /> لوحة التحكم
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate({ to: "/my-listings" })}>
                    <ListChecks className="ms-2 h-4 w-4" /> إعلاناتي
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate({ to: "/settings" })}>
                    <Settings className="ms-2 h-4 w-4" /> الإعدادات
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => {
                      logout();
                      navigate({ to: "/" });
                    }}
                    className="text-destructive focus:text-destructive"
                  >
                    <LogOut className="ms-2 h-4 w-4" /> تسجيل الخروج
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            <div className="hidden items-center gap-2 md:flex">
              <Link
                to="/login"
                className="rounded-md px-4 py-2 text-sm font-semibold text-primary hover:bg-secondary"
              >
                تسجيل الدخول
              </Link>
              <Link
                to="/register"
                className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary-light"
              >
                إنشاء حساب
              </Link>
            </div>
          )}

          {/* Mobile menu */}
          <Sheet>
            <SheetTrigger className="rounded-md p-2 hover:bg-secondary md:hidden" aria-label="القائمة">
              <Menu className="h-5 w-5" />
            </SheetTrigger>
            <SheetContent side="right" className="w-72">
              <div className="mt-6 flex flex-col gap-2">
                {NAV_LINKS.map((l) => (
                  <Link
                    key={l.to}
                    to={l.to}
                    className="rounded-md px-3 py-2.5 text-sm font-semibold hover:bg-secondary"
                  >
                    {l.label}
                  </Link>
                ))}
                <div className="my-2 h-px bg-border" />
                {!isLoggedIn ? (
                  <>
                    <Link to="/login" className="rounded-md px-3 py-2.5 text-sm font-semibold hover:bg-secondary">
                      <User className="ms-2 inline h-4 w-4" /> تسجيل الدخول
                    </Link>
                    <Link to="/register" className="rounded-md bg-primary px-3 py-2.5 text-center text-sm font-semibold text-primary-foreground">
                      إنشاء حساب
                    </Link>
                  </>
                ) : (
                  <>
                    <Link to="/dashboard" className="rounded-md px-3 py-2.5 text-sm font-semibold hover:bg-secondary">
                      لوحة التحكم
                    </Link>
                    <Link to="/my-listings" className="rounded-md px-3 py-2.5 text-sm font-semibold hover:bg-secondary">
                      إعلاناتي
                    </Link>
                  </>
                )}
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
