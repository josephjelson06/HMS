import { test, expect, type APIRequestContext } from "@playwright/test";

const BACKEND_BASE = process.env.PW_BACKEND_BASE_URL ?? "http://127.0.0.1:8000/api";
const FRONTEND_ORIGIN =
  process.env.PW_FRONTEND_ORIGIN ??
  process.env.PLAYWRIGHT_BASE_URL ??
  "http://localhost:3100";

async function getCookieValue(request: APIRequestContext, name: string): Promise<string | undefined> {
  const state = await request.storageState();
  return state.cookies.find((cookie) => cookie.name === name)?.value;
}

async function csrfHeaders(request: APIRequestContext): Promise<Record<string, string>> {
  const csrfToken = await getCookieValue(request, "csrf_token");
  if (!csrfToken) {
    throw new Error("Missing csrf_token cookie; call GET /auth/csrf first.");
  }
  return {
    "X-CSRF-Token": csrfToken,
    Origin: FRONTEND_ORIGIN
  };
}

async function apiLoginAdmin(request: APIRequestContext): Promise<void> {
  // Ensure we have a CSRF cookie for subsequent mutating requests.
  await request.get(`${BACKEND_BASE}/auth/csrf`);

  const loginResp = await request.post(`${BACKEND_BASE}/auth/login`, {
    data: { email: "admin@demo.com", password: "Admin123!" }
  });
  expect(loginResp.ok()).toBeTruthy();
}

async function apiGetDemoHotelTenantId(request: APIRequestContext): Promise<string> {
  const resp = await request.get(`${BACKEND_BASE}/admin/hotels?limit=50&page=1`);
  expect(resp.ok()).toBeTruthy();
  const json = (await resp.json()) as { items: Array<{ id: string; slug: string }> };
  const demo = json.items.find((item) => item.slug === "demo-hotel") ?? json.items[0];
  if (!demo) {
    throw new Error("No hotels returned from /admin/hotels; ensure SEED_DATA=true.");
  }
  return demo.id;
}

async function apiResolveDefaultHotelManagerId(request: APIRequestContext, tenantId: string): Promise<string> {
  // Start impersonation (returns the selected hotel user in response.user)
  const startResp = await request.post(`${BACKEND_BASE}/auth/impersonation/start`, {
    data: { tenant_id: tenantId, reason: "e2e" },
    headers: await csrfHeaders(request)
  });
  expect(startResp.ok()).toBeTruthy();
  const startJson = (await startResp.json()) as { user: { id: string } };
  const managerId = startJson.user.id;

  // Stop impersonation immediately to return to admin context (required for admin-only actions).
  const stopResp = await request.post(`${BACKEND_BASE}/auth/impersonation/stop`, {
    headers: await csrfHeaders(request)
  });
  expect(stopResp.ok()).toBeTruthy();

  return managerId;
}

async function apiResetPasswordForUser(request: APIRequestContext, userId: string): Promise<string> {
  const resp = await request.post(`${BACKEND_BASE}/auth/password/reset`, {
    data: { user_id: userId },
    headers: await csrfHeaders(request)
  });
  expect(resp.ok()).toBeTruthy();
  const json = (await resp.json()) as { temporary_password: string };
  return json.temporary_password;
}

test("admin can login and reach platform dashboard", async ({ page }) => {
  await page.goto("/login");

  await page.locator('input[type="email"]').fill("admin@demo.com");
  await page.locator('input[type="password"]').fill("Admin123!");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/admin\/dashboard$/);
  await expect(page.getByText("Platform Dashboard")).toBeVisible();
});

test("must-reset-password flow forces change-password then allows hotel workspace", async ({ page, playwright }) => {
  const api = await playwright.request.newContext({
    // API context keeps its own cookies, separate from the browser session.
    baseURL: "http://localhost"
  });
  try {
    await apiLoginAdmin(api);
    const tenantId = await apiGetDemoHotelTenantId(api);
    const managerUserId = await apiResolveDefaultHotelManagerId(api, tenantId);
    const tempPassword = await apiResetPasswordForUser(api, managerUserId);

    // Login as hotel manager using the temporary password (must_reset_password=true).
    await page.goto("/login");
    await page.locator('input[type="email"]').fill("manager@demo.com");
    await page.locator('input[type="password"]').fill(tempPassword);
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page).toHaveURL(/\/change-password$/);
    await expect(page.getByText("Reset your password")).toBeVisible();

    // Guard should prevent accessing hotel pages while must-reset is active.
    await page.goto("/hotel/dashboard");
    await expect(page).toHaveURL(/\/change-password$/);

    const newPassword = "NewStrongPass123!";

    await page.locator('label:text-is("Current Password")').locator("..").locator("input").fill(tempPassword);
    await page.locator('label:text-is("New Password")').locator("..").locator("input").fill(newPassword);
    await page.locator('label:text-is("Confirm New Password")').locator("..").locator("input").fill(newPassword);
    await page.getByRole("button", { name: "Change password" }).click();

    await expect(page).toHaveURL(/\/hotel\/dashboard$/);
    await expect(page.getByText("Hotel Dashboard")).toBeVisible();
  } finally {
    await api.dispose();
  }
});
