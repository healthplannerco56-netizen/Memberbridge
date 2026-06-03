/**
 * Clerk webhook handler.
 * Listens for user.created → creates workspace in Supabase via FastAPI.
 *
 * Setup in Clerk Dashboard:
 *   Webhooks → Add endpoint → https://yourapp.com/api/clerk-webhook
 *   Events: user.created
 *   Signing secret → CLERK_WEBHOOK_SECRET in .env
 */
import { headers } from "next/headers";
import { NextResponse } from "next/server";
import { Webhook } from "svix";

const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET;
const API_URL        = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(req: Request) {
  if (!WEBHOOK_SECRET) {
    console.error("CLERK_WEBHOOK_SECRET not set");
    return NextResponse.json({ error: "Server misconfigured" }, { status: 500 });
  }

  // Verify Svix signature
  const headerPayload = headers();
  const svix_id        = headerPayload.get("svix-id");
  const svix_timestamp = headerPayload.get("svix-timestamp");
  const svix_signature = headerPayload.get("svix-signature");

  if (!svix_id || !svix_timestamp || !svix_signature) {
    return NextResponse.json({ error: "Missing svix headers" }, { status: 400 });
  }

  const body = await req.text();
  const wh   = new Webhook(WEBHOOK_SECRET);

  let event: { type: string; data: Record<string, any> };
  try {
    event = wh.verify(body, {
      "svix-id":        svix_id,
      "svix-timestamp": svix_timestamp,
      "svix-signature": svix_signature,
    }) as typeof event;
  } catch (err) {
    console.error("Clerk webhook verification failed:", err);
    return NextResponse.json({ error: "Verification failed" }, { status: 401 });
  }

  // Handle user.created
  if (event.type === "user.created") {
    const { id: clerkUserId, email_addresses, first_name, last_name } = event.data;
    const email      = email_addresses?.[0]?.email_address ?? "";
    const name       = [first_name, last_name].filter(Boolean).join(" ") || email.split("@")[0];
    const workspaceName = `${name}'s Community`;

    try {
      // Call FastAPI to create workspace + default rules
      const resp = await fetch(`${API_URL}/api/v1/workspace/init`, {
        method:  "POST",
        headers: {
          "Content-Type":  "application/json",
          // Internal service key — set this in env for server-to-server calls
          "X-Service-Key": process.env.INTERNAL_SERVICE_KEY || "",
        },
        body: JSON.stringify({
          clerk_user_id: clerkUserId,
          email,
          name:          workspaceName,
        }),
      });

      if (!resp.ok) {
        const err = await resp.text();
        console.error("Failed to create workspace:", err);
        return NextResponse.json({ error: "Workspace creation failed" }, { status: 500 });
      }

      console.log(`Workspace created for user ${clerkUserId}`);
    } catch (err) {
      console.error("Error calling API:", err);
      return NextResponse.json({ error: "Internal error" }, { status: 500 });
    }
  }

  return NextResponse.json({ received: true });
}
