import LoginForm from "@/components/features/auth/login-form";
import { Badge } from "@/components/ui/primitives/badge";

export default function LoginPage() {
  return (
    <div className="glass-card auth-card">
      <div className="space-y-6">
        <div>
          <Badge>HMS Foundation</Badge>
          <h1 className="mt-4 text-3xl">Welcome back</h1>
          <p className="text-sm text-[color:var(--color-text-muted)]">
            Sign in to manage your platform or hotel workspace.
          </p>
        </div>
        <LoginForm />
      </div>
    </div>
  );
}
