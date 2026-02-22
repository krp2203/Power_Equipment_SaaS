"""
Email sending utilities for the application.
"""

from flask import render_template_string, current_app
from flask_mail import Mail, Message
from app.core.extensions import mail

def send_welcome_email(dealer_name, dealer_email, username, dealer_slug=None, temp_password=None):
    """
    Send a welcome email to a new dealer.

    Args:
        dealer_name (str): Name of the organization/dealer
        dealer_email (str): Email address of the dealer contact
        username (str): Username for login
        dealer_slug (str, optional): Dealer subdomain slug (e.g., 'kens-mowers')
        temp_password (str, optional): Temporary password if one was generated
    """
    try:
        # Get master organization contact info
        from app.core.models import Organization
        master_org = Organization.query.filter_by(slug='pes').first()
        support_email = "support@bentcrankshaft.com"
        support_phone = "(571) 238-8645"

        if master_org and master_org.theme_config:
            support_email = master_org.theme_config.get('contact_email', support_email)
            support_phone = master_org.theme_config.get('contact_phone', support_phone)

        subject = f"Welcome to Power Equipment SaaS - {dealer_name}"

        # Build login URL
        if dealer_slug:
            login_url = f"https://{dealer_slug}.bentcrankshaft.com/auth/login"
        else:
            login_url = "https://bentcrankshaft.com/auth/login"

        # Create HTML email body
        if temp_password:
            password_note = f"""
            <p><strong>Temporary Password:</strong> <code>{temp_password}</code></p>
            <p>Please change this password after your first login in your profile settings.</p>
            """
        else:
            password_note = "<p>You can now log in with your username and password.</p>"

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">Welcome to Power Equipment Dealer Portal! 🎉</h2>

                    <p>Hi {dealer_name},</p>

                    <p>Your dealer account has been successfully created! We're excited to have you on board.</p>

                    <h3>Your Login Information</h3>
                    <p>
                        <strong>Username:</strong> <code style="background: #f5f5f5; padding: 2px 6px; border-radius: 3px;">{username}</code><br>
                        {password_note}
                    </p>

                    <h3>Getting Started</h3>
                    <p>Once you log in, you'll be guided through our onboarding wizard where you can:</p>
                    <ul>
                        <li>Upload your company logo</li>
                        <li>Customize your website theme colors</li>
                        <li>Set up your contact information</li>
                        <li>Configure your inventory settings</li>
                    </ul>

                    <h3>Next Steps</h3>
                    <ol>
                        <li><strong>Log in</strong> to your account at <a href="{login_url}">{login_url}</a></li>
                        <li><strong>Complete onboarding</strong> - Takes about 5 minutes</li>
                        <li><strong>Explore your dashboard</strong> - Add inventory, manage parts, and more</li>
                    </ol>

                    <h3>Need Help?</h3>
                    <p>If you have any questions or need assistance, please don't hesitate to reach out:</p>
                    <ul>
                        <li>Email: <a href="mailto:{support_email}">{support_email}</a></li>
                        <li>Phone: <a href="tel:{support_phone.replace(' ', '').replace('(', '').replace(')', '').replace('-', '')}">{support_phone}</a></li>
                    </ul>

                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">

                    <p style="color: #666; font-size: 12px;">
                        This is an automated email. Please do not reply directly to this message.
                    </p>
                </div>
            </body>
        </html>
        """

        # Create plain text version
        text_body = f"""
Welcome to Power Equipment Dealer Portal!

Hi {dealer_name},

Your dealer account has been successfully created! We're excited to have you on board.

Your Login Information:
- Username: {username}
{f'- Temporary Password: {temp_password}' if temp_password else ''}
- Login URL: {login_url}

Getting Started:
Once you log in, you'll be guided through our onboarding wizard where you can:
- Upload your company logo
- Customize your website theme colors
- Set up your contact information
- Configure your inventory settings

Need Help?
- Email: {support_email}
- Phone: {support_phone}

This is an automated email. Please do not reply directly to this message.
        """

        # Create and send message
        # CC master dealer on all welcome emails
        cc_list = []
        if support_email and support_email != dealer_email:
            cc_list.append(support_email)

        msg = Message(
            subject=subject,
            recipients=[dealer_email],
            cc=cc_list,
            html=html_body,
            body=text_body,
            sender=current_app.config.get('MAIL_SENDER', 'noreply@mail.bentcrankshaft.com')
        )

        mail.send(msg)
        cc_info = f" (CC: {', '.join(cc_list)})" if cc_list else ""
        print(f"✅ Welcome email sent to {dealer_email}{cc_info}")
        return True

    except Exception as e:
        print(f"❌ Failed to send welcome email to {dealer_email}: {str(e)}")
        return False


def send_test_email(recipient_email):
    """
    Send a simple test email to verify mail configuration.

    Args:
        recipient_email (str): Email address to send test to
    """
    try:
        msg = Message(
            subject="Test Email from Power Equipment SaaS",
            recipients=[recipient_email],
            body="This is a test email to verify your mail configuration is working.",
            html="<p>This is a test email to verify your mail configuration is working.</p>",
            sender=current_app.config.get('MAIL_SENDER', 'noreply@mail.bentcrankshaft.com')
        )

        mail.send(msg)
        print(f"✅ Test email sent to {recipient_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send test email to {recipient_email}: {str(e)}")
        return False
