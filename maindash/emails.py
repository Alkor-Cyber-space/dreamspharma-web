from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_kyc_approval_email(user, kyc):
    """
    Send KYC approval email to the retailer
    
    Args:
        user: CustomUser instance (retailer)
        kyc: KYC instance
    """
    try:
        subject = 'KYC Approval - Welcome to Dream Pharma!'
        
        # Prepare email context
        context = {
            'retailer_name': user.first_name or user.username,
            'shop_name': kyc.shop_name,
            'approval_date': kyc.approved_at.strftime('%d-%m-%Y') if kyc.approved_at else 'N/A',
            'email': user.email,
        }
        
        # Create HTML email body
        html_message = f"""
      <html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KYC Approved – Dream Pharma</title>
</head>
<body style="margin:0;padding:20px 16px;background:#f0f4f2;font-family:Arial,sans-serif;">

  <table cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width:780px;margin:0 auto;">
    <tr><td>

    <!-- ── HEADER ── -->
    <table cellpadding="0" cellspacing="0" border="0" width="100%">
      <tr>
        <td style="background:linear-gradient(135deg,#0d6e65 0%,#0a5a52 60%,#084e47 100%);border-radius:16px 16px 0 0;padding:18px 30px;text-align:center;">

          <!-- Checkmark + Title inline -->
          <table cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;">
            <tr>
             
              <td style="vertical-align:middle;padding-left:12px;">
                <p style="font-family:Arial,sans-serif;font-size:9px;font-weight:bold;letter-spacing:2.5px;text-transform:uppercase;color:rgba(255,255,255,0.6);margin:0 0 2px 0;">Verification Status</p>
                <h1 style="font-family:Georgia,serif;font-size:24px;font-weight:bold;color:#ffffff;margin:0;">KYC <span style="color:#7dddd6;">Approved</span></h1>
              </td>
            </tr>
          </table>

        </td>
      </tr>
    </table>

    <!-- ── BODY ── -->
    <table cellpadding="0" cellspacing="0" border="0" width="100%">
      <tr>
        <td style="background:#ffffff;padding:24px 36px;">

          <!-- Greeting -->
          <p style="font-family:Georgia,serif;font-size:16px;font-weight:bold;color:#0a5a52;margin:0 0 6px 0;">Dear {context['retailer_name']},</p>
          <p style="font-size:13px;color:#4a5568;line-height:1.6;margin:0 0 20px 0;">Congratulations! Your KYC verification has been <strong style="color:#1a2e2b;">successfully approved</strong>. Your pharmacy account is now active and ready to use.</p>

          <!-- ── Details Card ── -->
          <table cellpadding="0" cellspacing="0" border="0" width="100%" style="border:1px solid #e2ede9;border-radius:12px;border-collapse:separate;border-spacing:0;margin-bottom:20px;overflow:hidden;">

            <!-- Card header -->
            <tr>
              <td colspan="2" style="background:#f5fbf9;padding:10px 16px;border-bottom:1px solid #e2ede9;">
                <span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#0d6e65;vertical-align:middle;margin-right:7px;"></span>
                <span style="font-size:9px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;color:#0d6e65;vertical-align:middle;">Approval Details</span>
              </td>
            </tr>

            <!-- Shop Name -->
            <tr>
              <td style="width:50px;padding:12px 0 12px 16px;vertical-align:middle;border-bottom:1px solid #f0f4f2;">
                <table cellpadding="0" cellspacing="0" border="0"><tr>
                  <td style="width:32px;height:32px;border-radius:8px;background:#f0faf8;text-align:center;vertical-align:middle;font-size:16px;line-height:32px;">🏪</td>
                </tr></table>
              </td>
              <td style="padding:12px 16px;border-bottom:1px solid #f0f4f2;vertical-align:middle;">
                <p style="font-size:9px;font-weight:bold;letter-spacing:1.5px;text-transform:uppercase;color:#94a3b8;margin:0 0 2px 0;">Shop Name</p>
                <p style="font-size:13px;font-weight:bold;color:#1a2e2b;margin:0;">{context['shop_name']}</p>
              </td>
            </tr>

            <!-- Approval Date -->
            <tr>
              <td style="width:50px;padding:12px 0 12px 16px;vertical-align:middle;border-bottom:1px solid #f0f4f2;">
                <table cellpadding="0" cellspacing="0" border="0"><tr>
                  <td style="width:32px;height:32px;border-radius:8px;background:#f0faf8;text-align:center;vertical-align:middle;font-size:16px;line-height:32px;">📅</td>
                </tr></table>
              </td>
              <td style="padding:12px 16px;border-bottom:1px solid #f0f4f2;vertical-align:middle;">
                <p style="font-size:9px;font-weight:bold;letter-spacing:1.5px;text-transform:uppercase;color:#94a3b8;margin:0 0 2px 0;">Approval Date</p>
                <p style="font-size:13px;font-weight:bold;color:#1a2e2b;margin:0;">{context['approval_date']}</p>
              </td>
            </tr>

            <!-- Registered Email -->
            <tr>
              <td style="width:50px;padding:12px 0 12px 16px;vertical-align:middle;">
                <table cellpadding="0" cellspacing="0" border="0"><tr>
                  <td style="width:32px;height:32px;border-radius:8px;background:#f0faf8;text-align:center;vertical-align:middle;font-size:16px;line-height:32px;">📧</td>
                </tr></table>
              </td>
              <td style="padding:12px 16px;vertical-align:middle;">
                <p style="font-size:9px;font-weight:bold;letter-spacing:1.5px;text-transform:uppercase;color:#94a3b8;margin:0 0 2px 0;">Registered Email</p>
                <a href="mailto:{context['email']}" style="font-size:13px;font-weight:bold;color:#0d6e65;text-decoration:none;">{context['email']}</a>
              </td>
            </tr>

          </table>

          <!-- Success note -->
          <table cellpadding="0" cellspacing="0" border="0" width="100%">
            <tr>
              <td style="background:#f0faf8;border-left:3px solid #0d6e65;border-radius:0 8px 8px 0;padding:12px 16px;">
                <p style="font-size:12px;color:#2d5a55;line-height:1.6;margin:0;">You can now proceed with your account activation. Your account will be fully activated shortly. For any questions, please contact our support team.</p>
              </td>
            </tr>
          </table>

        </td>
      </tr>
    </table>


    </td></tr>
  </table>

</body>
</html>
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=f"Dear {context['retailer_name']},\n\nCongratulations! Your KYC verification has been approved.\n\nShop Name: {context['shop_name']}\nApproval Date: {context['approval_date']}\n\nBest regards,\nDream Pharma Team",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Error sending KYC approval email to {user.email}: {str(e)}")
        return False


def send_kyc_rejection_email(user, kyc, rejection_reason):
    """
    Send KYC rejection email to the retailer with reason
    
    Args:
        user: CustomUser instance (retailer)
        kyc: KYC instance
        rejection_reason: Reason for rejection
    """
    try:
        from django.utils import timezone
        subject = 'KYC Rejection - Action Required'
        
        # Prepare email context
        context = {
            'retailer_name': user.first_name or user.username,
            'shop_name': kyc.shop_name,
            'rejection_reason': rejection_reason,
            'rejection_date': timezone.now().strftime('%d-%m-%Y'),
            'email': user.email,
        }
        
        # Create HTML email body
        html_message = f"""
     <html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KYC Rejected – Dream Pharma</title>
</head>
<body style="margin:0;padding:20px 16px;background:#f9f0f0;font-family:Arial,sans-serif;">

  <table cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width:780px;margin:0 auto;">
    <tr><td>

      <!-- HEADER -->
      <table cellpadding="0" cellspacing="0" border="0" width="100%">
        <tr>
          <td style="background:linear-gradient(135deg,#c0392b 0%,#922b21 100%);border-radius:16px 16px 0 0;padding:18px 30px;text-align:center;">
            <p style="font-size:9px;font-weight:bold;letter-spacing:2.5px;text-transform:uppercase;color:rgba(255,255,255,0.6);margin:0 0 4px 0;">Verification Status</p>
            <h1 style="font-family:Georgia,serif;font-size:24px;font-weight:bold;color:#ffffff;margin:0;">KYC <span style="color:#f1948a;">Rejected</span></h1>
          </td>
        </tr>
      </table>

      <!-- BODY -->
      <table cellpadding="0" cellspacing="0" border="0" width="100%">
        <tr>
          <td style="background:#ffffff;padding:24px 30px;">

            <p style="font-family:Georgia,serif;font-size:15px;font-weight:bold;color:#922b21;margin:0 0 6px 0;">Dear {context['retailer_name']},</p>
            <p style="font-size:13px;color:#4a5568;line-height:1.6;margin:0 0 20px 0;">We regret to inform you that your KYC verification has been <strong style="color:#c0392b;">rejected</strong>. Please review the details below.</p>

            <!-- Details -->
            <table cellpadding="0" cellspacing="0" border="0" width="100%" style="border:1px solid #f5c6c2;border-radius:10px;border-collapse:separate;border-spacing:0;margin-bottom:16px;overflow:hidden;">
              <tr>
                <td colspan="2" style="background:#fdf3f2;padding:9px 16px;border-bottom:1px solid #f5c6c2;">
                  <span style="font-size:9px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;color:#c0392b;">Rejection Details</span>
                </td>
              </tr>
              <!-- Shop Name -->
              <tr>
                <td style="width:50px;padding:12px 0 12px 16px;vertical-align:middle;border-bottom:1px solid #fdf0ef;">
                  <table cellpadding="0" cellspacing="0" border="0"><tr>
                    <td style="width:32px;height:32px;border-radius:8px;background:#fdf3f2;text-align:center;vertical-align:middle;font-size:16px;line-height:32px;">🏪</td>
                  </tr></table>
                </td>
                <td style="padding:12px 16px;border-bottom:1px solid #fdf0ef;vertical-align:middle;">
                  <p style="font-size:9px;font-weight:bold;letter-spacing:1.5px;text-transform:uppercase;color:#94a3b8;margin:0 0 2px 0;">Shop Name</p>
                  <p style="font-size:13px;font-weight:bold;color:#1a2e2b;margin:0;">{context['shop_name']}</p>
                </td>
              </tr>
              <!-- Rejection Date -->
              <tr>
                <td style="width:50px;padding:12px 0 12px 16px;vertical-align:middle;border-bottom:1px solid #fdf0ef;">
                  <table cellpadding="0" cellspacing="0" border="0"><tr>
                    <td style="width:32px;height:32px;border-radius:8px;background:#fdf3f2;text-align:center;vertical-align:middle;font-size:16px;line-height:32px;">📅</td>
                  </tr></table>
                </td>
                <td style="padding:12px 16px;border-bottom:1px solid #fdf0ef;vertical-align:middle;">
                  <p style="font-size:9px;font-weight:bold;letter-spacing:1.5px;text-transform:uppercase;color:#94a3b8;margin:0 0 2px 0;">Rejection Date</p>
                  <p style="font-size:13px;font-weight:bold;color:#1a2e2b;margin:0;">{context['rejection_date']}</p>
                </td>
              </tr>
              <!-- Reason -->
              <tr>
                <td style="width:50px;padding:12px 0 12px 16px;vertical-align:middle;border-bottom:1px solid #fdf0ef;">
                  <table cellpadding="0" cellspacing="0" border="0"><tr>
                    <td style="width:32px;height:32px;border-radius:8px;background:#fdf3f2;text-align:center;vertical-align:middle;font-size:16px;line-height:32px;">⚠️</td>
                  </tr></table>
                </td>
                <td style="padding:12px 16px;border-bottom:1px solid #fdf0ef;vertical-align:middle;">
                  <p style="font-size:9px;font-weight:bold;letter-spacing:1.5px;text-transform:uppercase;color:#94a3b8;margin:0 0 2px 0;">Reason</p>
                  <p style="font-size:13px;font-weight:bold;color:#c0392b;margin:0;">{context['rejection_reason']}</p>
                </td>
              </tr>
              <!-- Email -->
              <tr>
                <td style="width:50px;padding:12px 0 12px 16px;vertical-align:middle;">
                  <table cellpadding="0" cellspacing="0" border="0"><tr>
                    <td style="width:32px;height:32px;border-radius:8px;background:#fdf3f2;text-align:center;vertical-align:middle;font-size:16px;line-height:32px;">📧</td>
                  </tr></table>
                </td>
                <td style="padding:12px 16px;vertical-align:middle;">
                  <p style="font-size:9px;font-weight:bold;letter-spacing:1.5px;text-transform:uppercase;color:#94a3b8;margin:0 0 2px 0;">Email</p>
                  <a href="mailto:{context['email']}" style="font-size:13px;font-weight:bold;color:#c0392b;text-decoration:none;">{context['email']}</a>
                </td>
              </tr>
            </table>

          </td>
        </tr>
      </table>

    </td></tr>
  </table>

</body>
</html>
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=f"Dear {context['retailer_name']},\n\nYour KYC verification has been rejected.\n\nReason: {context['rejection_reason']}\n\nPlease contact our support team for further assistance.\n\nBest regards,\nDream Pharma Team",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Error sending KYC rejection email to {user.email}: {str(e)}")
        return False
