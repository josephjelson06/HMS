"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { InlineAlert } from "@/components/ui/composed/inline-alert";
import { Button } from "@/components/ui/primitives/button";
import { Field } from "@/components/ui/primitives/field";
import { TextInput } from "@/components/ui/primitives/text-input";
import { useAuth } from "@/lib/hooks/use-auth";

export default function LoginForm() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const response = await login(email, password);
      if (response.must_reset_password) {
        router.push("/change-password");
        return;
      }

      const isPlatformUser =
        response.user.user_type === "platform" || response.user.user_type === "admin";
      const target = isPlatformUser ? "/admin/dashboard" : "/hotel/dashboard";
      router.push(target);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Login failed";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Field label="Email">
        <TextInput
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@company.com"
        />
      </Field>
      <Field label="Password">
        <TextInput
          type="password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="********"
        />
      </Field>
      {error ? <InlineAlert tone="error" message={error} /> : null}
      <Button type="submit" variant="primary" className="w-full" disabled={submitting}>
        {submitting ? "Signing in..." : "Sign in"}
      </Button>
    </form>
  );
}
