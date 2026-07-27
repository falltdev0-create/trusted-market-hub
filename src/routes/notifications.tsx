import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCircle2, AlertTriangle, Info, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { MOCK_NOTIFICATIONS } from "@/lib/mock-data";
import { notificationsApi, tryApi } from "@/lib/api";
import { EmptyState } from "@/components/EmptyState";
import { useAuthStore } from "@/stores/auth";

export const Route = createFileRoute("/notifications")({
  head: () => ({ meta: [{ title: "الإشعارات — مسكن" }] }),
  component: NotificationsPage,
});

interface Notif {
  id: string;
  type: "success" | "warning" | "info";
  title: string;
  desc?: string;
  message?: string;
  time?: string;
  created_at?: string;
  read: boolean;
}

const ICONS = {
  success: { i: CheckCircle2, c: "text-success bg-success/10" },
  warning: { i: AlertTriangle, c: "text-warning bg-warning/10" },
  info: { i: Info, c: "text-primary bg-primary/10" },
};

function NotificationsPage() {
  const qc = useQueryClient();
  const { isLoggedIn } = useAuthStore();

  const { data, isLoading } = useQuery<Notif[]>({
    queryKey: ["notifications"],
    queryFn: () =>
      tryApi(
        () => notificationsApi.list().then((r) => (Array.isArray(r.data) ? r.data : r.data?.items ?? [])),
        MOCK_NOTIFICATIONS as any,
      ),
    enabled: isLoggedIn,
  });

  const markOne = useMutation({
    mutationFn: (id: string) => tryApi(() => notificationsApi.markRead(id).then((r) => r.data), { ok: true }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAll = useMutation({
    mutationFn: () => tryApi(() => notificationsApi.markAllRead().then((r) => r.data), { ok: true }),
    onSuccess: () => {
      toast.success("تم تعليم جميع الإشعارات كمقروءة");
      qc.invalidateQueries({ queryKey: ["notifications"] });
      qc.invalidateQueries({ queryKey: ["notifications", "unread-count"] });
    },
  });

  const items = data ?? [];

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <Bell className="h-6 w-6 text-primary" /> الإشعارات
        </h1>
        <button
          onClick={() => markAll.mutate()}
          disabled={markAll.isPending || items.every((n) => n.read)}
          className="inline-flex items-center gap-1 text-sm font-semibold text-primary hover:underline disabled:opacity-50"
        >
          {markAll.isPending && <Loader2 className="h-3 w-3 animate-spin" />}
          تعليم الكل كمقروء
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
      ) : items.length === 0 ? (
        <EmptyState icon={Bell} title="لا توجد إشعارات" description="كل شيء على ما يرام!" />
      ) : (
        <ul className="space-y-2">
          {items.map((n) => {
            const k = ICONS[(n.type as keyof typeof ICONS) ?? "info"] ?? ICONS.info;
            const Ic = k.i;
            return (
              <li
                key={n.id}
                className={`flex cursor-pointer items-start gap-3 rounded-xl border bg-card p-4 transition hover:bg-secondary/50 ${
                  !n.read ? "border-primary/30 bg-primary/5" : ""
                }`}
                onClick={() => !n.read && markOne.mutate(n.id)}
              >
                <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${k.c}`}>
                  <Ic className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <div className={`text-sm ${!n.read ? "font-bold" : "font-semibold"}`}>{n.title}</div>
                  <div className="mt-0.5 text-sm text-muted-foreground">{n.desc ?? n.message}</div>
                  <div className="mt-1 text-xs text-muted-foreground">{n.time ?? n.created_at}</div>
                </div>
                {!n.read && <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" />}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
