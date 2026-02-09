import http from "k6/http";
import { check, sleep } from "k6";

/*
Phase 5 (Performance + Reliability) — k6 suite

Designed to be run against a disposable DB created via:
  scripts/perf/New-HmsPerfDb.ps1

Defaults assume a backend at http://127.0.0.1:8000/api and frontend origin http://localhost:3000.
If running k6 inside Docker, set K6_BASE_URL=http://host.docker.internal:8000/api.
*/

const BASE_URL = (__ENV.K6_BASE_URL || "http://127.0.0.1:8000/api").replace(/\/+$/, "");
const ORIGIN = (__ENV.K6_ORIGIN || "http://localhost:3000").replace(/\/+$/, "");

const ADMIN_EMAIL = __ENV.K6_ADMIN_EMAIL || "admin@demo.com";
const ADMIN_PASSWORD = __ENV.K6_ADMIN_PASSWORD || "Admin123!";
const HOTEL_EMAIL = __ENV.K6_HOTEL_EMAIL || "manager@demo.com";
const HOTEL_PASSWORD = __ENV.K6_HOTEL_PASSWORD || "Manager123!";

const DURATION = __ENV.K6_DURATION || "2m";

const VUS_ADMIN = parseInt(__ENV.K6_VUS_ADMIN || "5", 10);
const VUS_HOTEL_REFRESH = parseInt(__ENV.K6_VUS_HOTEL_REFRESH || "10", 10);
const VUS_HOTEL_CRUD = parseInt(__ENV.K6_VUS_HOTEL_CRUD || "10", 10);

const THRESH_P95_REFRESH_MS = parseInt(__ENV.K6_THRESH_P95_REFRESH_MS || "250", 10);
const THRESH_P95_CRUD_MS = parseInt(__ENV.K6_THRESH_P95_CRUD_MS || "400", 10);

export const options = {
  discardResponseBodies: true,
  thresholds: {
    http_req_failed: ["rate<0.01"],
    [`http_req_duration{req_name:auth_refresh}`]: [`p(95)<${THRESH_P95_REFRESH_MS}`],
    [`http_req_duration{req_name:hotel_room_create}`]: [`p(95)<${THRESH_P95_CRUD_MS}`],
    [`http_req_duration{req_name:hotel_room_list}`]: [`p(95)<${THRESH_P95_CRUD_MS}`],
  },
  scenarios: {
    admin_browse: {
      executor: "constant-vus",
      vus: VUS_ADMIN,
      duration: DURATION,
      exec: "adminBrowse",
    },
    hotel_refresh_loop: {
      executor: "constant-vus",
      vus: VUS_HOTEL_REFRESH,
      duration: DURATION,
      exec: "hotelRefreshLoop",
    },
    hotel_room_crud: {
      executor: "constant-vus",
      vus: VUS_HOTEL_CRUD,
      duration: DURATION,
      exec: "hotelRoomCrud",
    },
  },
};

function originHeaders() {
  return { Origin: ORIGIN };
}

function getCookieValue(jar, url, name) {
  const cookies = jar.cookiesForURL(url);
  const values = cookies[name];
  if (!values || values.length === 0) return null;
  return values[0].value;
}

function ensureCsrfCookie(jar) {
  const existing = getCookieValue(jar, BASE_URL, "csrf_token");
  if (existing) return existing;

  const r = http.get(`${BASE_URL}/auth/csrf`, { headers: originHeaders(), tags: { req_name: "auth_csrf" } });
  check(r, { "csrf: status 200": (res) => res.status === 200 });

  const csrf = getCookieValue(jar, BASE_URL, "csrf_token");
  check(csrf, { "csrf cookie present": (v) => !!v });
  return csrf;
}

function csrfHeaders(jar) {
  const csrf = ensureCsrfCookie(jar);
  return {
    ...originHeaders(),
    "X-CSRF-Token": csrf,
  };
}

function login(jar, email, password, tagName) {
  // Login is exempt from CSRF double-submit, but we still prefetch CSRF cookie to mimic browser flow.
  ensureCsrfCookie(jar);

  const payload = JSON.stringify({ email, password });
  const r = http.post(`${BASE_URL}/auth/login`, payload, {
    headers: { ...originHeaders(), "Content-Type": "application/json" },
    tags: { req_name: tagName || "auth_login" },
  });
  check(r, { "login: status 200": (res) => res.status === 200 });

  // Cookie presence sanity.
  const at = getCookieValue(jar, BASE_URL, "access_token");
  const rt = getCookieValue(jar, BASE_URL, "refresh_token");
  check(at, { "access_token cookie present": (v) => !!v });
  check(rt, { "refresh_token cookie present": (v) => !!v });
}

function authMe(jar, tagName) {
  const r = http.get(`${BASE_URL}/auth/me`, { headers: originHeaders(), tags: { req_name: tagName || "auth_me" } });
  check(r, { "me: status 200": (res) => res.status === 200 });
  return r;
}

function authRefresh(jar) {
  const r = http.post(`${BASE_URL}/auth/refresh`, null, { headers: originHeaders(), tags: { req_name: "auth_refresh" } });
  check(r, { "refresh: status 200": (res) => res.status === 200 });
  return r;
}

export function adminBrowse() {
  const jar = http.cookieJar();
  login(jar, ADMIN_EMAIL, ADMIN_PASSWORD, "admin_login");

  // Admin endpoints (read-only)
  const hotels = http.get(`${BASE_URL}/admin/hotels/`, { headers: originHeaders(), tags: { req_name: "admin_hotels_list" } });
  check(hotels, { "admin hotels: 200": (r) => r.status === 200 });

  const audits = http.get(`${BASE_URL}/admin/audit/`, { headers: originHeaders(), tags: { req_name: "admin_audit_list" } });
  check(audits, { "admin audit: 200": (r) => r.status === 200 });

  // Small sleep to avoid tight-looping.
  sleep(0.2);
}

export function hotelRefreshLoop() {
  const jar = http.cookieJar();
  login(jar, HOTEL_EMAIL, HOTEL_PASSWORD, "hotel_login");

  // Hot path: refresh + me (verifies auth state stays valid).
  authRefresh(jar);
  authMe(jar, "hotel_me");

  sleep(0.2);
}

export function hotelRoomCrud() {
  const jar = http.cookieJar();
  login(jar, HOTEL_EMAIL, HOTEL_PASSWORD, "hotel_login_crud");

  // Create a room (mutating => CSRF header required).
  const roomNumber = `K6-${__VU}-${Date.now()}`;
  const createPayload = JSON.stringify({ number: roomNumber, room_type: "standard" });
  const create = http.post(`${BASE_URL}/hotel/rooms/`, createPayload, {
    headers: { ...csrfHeaders(jar), "Content-Type": "application/json" },
    tags: { req_name: "hotel_room_create" },
  });
  check(create, { "room create: 201": (r) => r.status === 201 });

  // List rooms (read-only).
  const list = http.get(`${BASE_URL}/hotel/rooms/`, { headers: originHeaders(), tags: { req_name: "hotel_room_list" } });
  check(list, { "room list: 200": (r) => r.status === 200 });

  sleep(0.2);
}

