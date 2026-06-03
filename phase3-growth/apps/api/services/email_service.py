"""
Email service using Resend.
Handles transactional and dunning emails.
"""
import logging
import resend
from config import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.resend_api_key


class EmailService:

    async def send(
        self,
        to: str,
        subject: str,
        html: str,
        from_name: str | None = None,
    ) -> str | None:
        """Send a single email. Returns Resend message ID or None on failure."""
        from_addr = f"{from_name or settings.resend_from_name} <{settings.resend_from_email}>"
        try:
            resp = resend.Emails.send({
                "from":    from_addr,
                "to":      [to],
                "subject": subject,
                "html":    html,
            })
            logger.info(f"Email sent to {to}: {resp['id']}")
            return resp["id"]
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return None

    def render_failed_payment(
        self,
        member_name: str | None,
        community_name: str,
        step: int,
        retry_url: str | None = None,
    ) -> tuple[str, str]:
        """Returns (subject, html) for a dunning email step."""
        name = member_name or "there"

        templates = {
            1: {
                "subject": f"Action needed: Payment failed for {community_name}",
                "html": f"""
<div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px;color:#1a1a1a">
  <h2 style="margin:0 0 16px">Hi {name},</h2>
  <p>We weren't able to process your payment for <strong>{community_name}</strong>.</p>
  <p>Your access is still active for now. Please update your payment details to avoid interruption.</p>
  {f'<a href="{retry_url}" style="display:inline-block;background:#7c3aed;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;margin-top:8px">Update Payment</a>' if retry_url else ''}
  <p style="color:#666;margin-top:24px;font-size:14px">If you have questions, reply to this email.</p>
</div>""",
            },
            2: {
                "subject": f"Reminder: Payment still pending for {community_name}",
                "html": f"""
<div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px;color:#1a1a1a">
  <h2 style="margin:0 0 16px">Hi {name},</h2>
  <p>This is a reminder that your payment for <strong>{community_name}</strong> is still outstanding.</p>
  <p>Your access may be restricted soon. Please update your details now.</p>
  {f'<a href="{retry_url}" style="display:inline-block;background:#7c3aed;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;margin-top:8px">Update Payment</a>' if retry_url else ''}
</div>""",
            },
            3: {
                "subject": f"Final notice: Your {community_name} access will be cancelled",
                "html": f"""
<div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px;color:#1a1a1a">
  <h2 style="margin:0 0 16px">Hi {name},</h2>
  <p>This is your final notice. Your access to <strong>{community_name}</strong> will be cancelled in 24 hours if payment is not received.</p>
  {f'<a href="{retry_url}" style="display:inline-block;background:#dc2626;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;margin-top:8px">Resolve Now</a>' if retry_url else ''}
  <p style="color:#666;margin-top:24px;font-size:14px">We hope to keep you as a member.</p>
</div>""",
            },
        }

        t = templates.get(step, templates[1])
        return t["subject"], t["html"]
