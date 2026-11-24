// Supabase edge function `analytics` (Deno), served as GET /analytics (4.B4 slice 2; FR-P01, FR-P04). Logic and requirement IDs: ../_shared/analytics.ts. Contract: docs/interfaces/openapi.yaml.
import { handleAnalytics } from "../_shared/analytics.ts";
import { makeAnalyticsDeps } from "../_shared/supabase.ts";

Deno.serve((req) => handleAnalytics(req, makeAnalyticsDeps()));
