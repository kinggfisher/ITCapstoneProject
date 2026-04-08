import resend as resend_sdk
from django.conf import settings
from django.core.mail import send_mail


def _build_subject(assessment):
    return f"⚠️ Compliance Check FAILED – {assessment.asset.name}"


def _build_plain(user, assessment):
    return f"""Compliance Check Failed

Asset:          {assessment.asset.name}
Location:       {assessment.asset.location.name}
Equipment Type: {assessment.get_equipment_type_display()}
Equipment Model:{assessment.equipment_model or '—'}
Load Applied:   {assessment.load_value} {assessment.capacity_metric}
Capacity Limit: {assessment.capacity_limit} {assessment.capacity_metric}
Checked By:     {user.username}
{f'Notes:          {assessment.notes}' if assessment.notes else ''}

This is an automated alert from AssetGuard. Do not reply to this email.
"""


def _build_html(user, assessment):
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #ef4444; padding: 16px 24px; border-radius: 8px 8px 0 0;">
            <h2 style="color: white; margin: 0;">⚠️ Compliance Check Failed</h2>
        </div>
        <div style="background: #f9fafb; padding: 24px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
            <p style="color: #374151; font-size: 15px;">
                Hi <strong>{user.get_full_name() or user.username}</strong>,
            </p>
            <p style="color: #374151; font-size: 15px;">
                A compliance check on <strong>{assessment.asset.name}</strong> has
                <span style="color: #ef4444; font-weight: bold;">FAILED</span>.
                Here are the details:
            </p>
            <table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px;">
                <tr style="background: #f3f4f6;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #6b7280; width: 40%;">Location</td>
                    <td style="padding: 10px 14px; color: #111827;">{assessment.asset.location.name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 14px; font-weight: bold; color: #6b7280;">Asset</td>
                    <td style="padding: 10px 14px; color: #111827;">{assessment.asset.name}</td>
                </tr>
                <tr style="background: #f3f4f6;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #6b7280;">Equipment Type</td>
                    <td style="padding: 10px 14px; color: #111827;">{assessment.get_equipment_type_display()}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 14px; font-weight: bold; color: #6b7280;">Equipment Model</td>
                    <td style="padding: 10px 14px; color: #111827;">{assessment.equipment_model or '—'}</td>
                </tr>
                <tr style="background: #f3f4f6;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #6b7280;">Load Applied</td>
                    <td style="padding: 10px 14px; color: #ef4444; font-weight: bold;">
                        {assessment.load_value} {assessment.capacity_metric}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 14px; font-weight: bold; color: #6b7280;">Capacity Limit</td>
                    <td style="padding: 10px 14px; color: #111827;">
                        {assessment.capacity_limit} {assessment.capacity_metric}
                    </td>
                </tr>
                <tr style="background: #f3f4f6;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #6b7280;">Checked By</td>
                    <td style="padding: 10px 14px; color: #111827;">{user.username}</td>
                </tr>
                {"<tr><td style='padding: 10px 14px; font-weight: bold; color: #6b7280;'>Notes</td><td style='padding: 10px 14px; color: #111827;'>" + assessment.notes + "</td></tr>" if assessment.notes else ""}
            </table>
            <p style="color: #6b7280; font-size: 13px; margin-top: 24px; border-top: 1px solid #e5e7eb; padding-top: 16px;">
                This is an automated alert from <strong>AssetGuard</strong>. Do not reply to this email.
            </p>
        </div>
    </div>
    """


def _send_via_gmail(user, assessment):
    """Send alert using Django's built-in Gmail SMTP backend."""
    if not settings.EMAIL_HOST_USER:
        print("[email_utils] Warning: EMAIL_HOST_USER is not set. Skipping Gmail alert.")
        return

    send_mail(
        subject=_build_subject(assessment),
        message=_build_plain(user, assessment),
        from_email=f"AssetGuard Alerts <{settings.EMAIL_HOST_USER}>",
        recipient_list=[user.email],
        html_message=_build_html(user, assessment),
        fail_silently=False,
    )


def _send_via_resend(user, assessment):
    """Send alert using the Resend API."""
    if not settings.RESEND_API_KEY:
        print("[email_utils] Warning: RESEND_API_KEY is not set. Skipping Resend alert.")
        return

    resend_sdk.api_key = settings.RESEND_API_KEY
    resend_sdk.Emails.send({
        "from": "AssetGuard Alerts <onboarding@resend.dev>",
        "to": [user.email],
        "subject": _build_subject(assessment),
        "html": _build_html(user, assessment),
    })


def send_compliance_failure_alert(user, assessment):
    """
    Send an email alert to the user when a compliance check fails.

    Controlled by env vars:
      EMAIL_ALERTS=true/false     — master on/off switch
      EMAIL_PROVIDER=gmail/resend — which provider to use

    Gmail requires: EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
    Resend requires: RESEND_API_KEY

    This function is a no-op if EMAIL_ALERTS_ENABLED is False or
    the user has no registered email address.
    """
    if not settings.EMAIL_ALERTS_ENABLED:
        return

    if not user.email:
        return

    provider = settings.EMAIL_PROVIDER.lower()

    try:
        if provider == 'resend':
            _send_via_resend(user, assessment)
        else:
            # Default to Gmail SMTP
            _send_via_gmail(user, assessment)
    except Exception as e:
        # Log but don't raise — email failure should never break the API response
        print(f"[email_utils] Failed to send compliance alert via {provider}: {e}")
