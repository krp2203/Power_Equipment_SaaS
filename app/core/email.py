"""
Email sending utilities for the application.
"""

from flask import render_template_string, current_app
from flask_mail import Mail, Message
from app.core.extensions import mail

def send_dealer_admin_notification(dealer_name, dealer_slug, custom_domain=None, temp_admin_password=None, admin_username=None):
    """
    Send a notification to SaaS admin (ken@bentcrankshaft.com) with dealer setup details.

    Args:
        dealer_name (str): Name of the dealer
        dealer_slug (str): Dealer subdomain slug
        custom_domain (str, optional): Custom domain if provided
        temp_admin_password (str, optional): Temp admin password for impersonation
        admin_username (str, optional): Admin username
    """
    try:
        admin_email = "ken@bentcrankshaft.com"

        subject = f"New Dealer Created: {dealer_name}"

        # Build HTML email
        domain_section = ""
        if custom_domain:
            domain_section = f"""
            <h3>Custom Domain Setup Required ⚠️</h3>
            <p><strong>Custom Domain:</strong> {custom_domain}</p>
            <p>To complete setup, you'll need to:</p>
            <ol>
                <li><strong>Request SSL Certificate:</strong>
                    <code style="background: #f5f5f5; padding: 4px 8px; border-radius: 3px; display: block; margin: 10px 0;">
                    certbot certonly --standalone -d {custom_domain}
                    </code>
                </li>
                <li><strong>Add Nginx Config:</strong> Create server block in /etc/nginx/sites-enabled/ with:
                    <code style="background: #f5f5f5; padding: 4px 8px; border-radius: 3px; display: block; margin: 10px 0;">
                    server_name {custom_domain} www.{custom_domain};<br>
                    ssl_certificate /etc/letsencrypt/live/{custom_domain}/fullchain.pem;<br>
                    ssl_certificate_key /etc/letsencrypt/live/{custom_domain}/privkey.pem;
                    </code>
                </li>
                <li><strong>Reload Nginx:</strong>
                    <code style="background: #f5f5f5; padding: 4px 8px; border-radius: 3px; display: block; margin: 10px 0;">
                    nginx -t && systemctl reload nginx
                    </code>
                </li>
                <li><strong>Inform Dealer:</strong> They must point DNS:
                    <code style="background: #f5f5f5; padding: 4px 8px; border-radius: 3px; display: block; margin: 10px 0;">
                    {custom_domain} CNAME bentcrankshaft.com
                    </code>
                </li>
            </ol>
            """

        impersonate_section = ""
        if temp_admin_password and admin_username:
            impersonate_section = f"""
            <h3>Impersonate Dealer (Testing)</h3>
            <p>To test as this dealer:</p>
            <code style="background: #f5f5f5; padding: 4px 8px; border-radius: 3px; display: block; margin: 10px 0;">
            Username: {admin_username}<br>
            Password: {temp_admin_password}
            </code>
            <p>Then use the "Impersonate" feature from the dashboard.</p>
            """

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">New Dealer Created ✨</h2>

                    <h3>Dealer Details</h3>
                    <p>
                        <strong>Name:</strong> {dealer_name}<br>
                        <strong>Slug:</strong> {dealer_slug}<br>
                        <strong>Subdomain:</strong> https://{dealer_slug}.bentcrankshaft.com<br>
                    </p>

                    {domain_section}

                    {impersonate_section}

                    <h3>Next Steps Checklist</h3>
                    <ul>
                        <li>☐ Dealer receives welcome email with login instructions</li>
                        <li>☐ Dealer logs in and completes onboarding</li>
                        {f'<li>☐ Request SSL cert for {custom_domain}</li>' if custom_domain else ''}
                        {f'<li>☐ Add nginx config for {custom_domain}</li>' if custom_domain else ''}
                        {f'<li>☐ Dealer configures DNS for {custom_domain}</li>' if custom_domain else ''}
                        <li>☐ Verify all images and functionality working</li>
                    </ul>

                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                    <p style="color: #666; font-size: 12px;">
                        This is an automated notification. Do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """

        text_body = f"""
New Dealer Created

Name: {dealer_name}
Slug: {dealer_slug}
Subdomain: https://{dealer_slug}.bentcrankshaft.com
{"Custom Domain: " + custom_domain if custom_domain else ""}

{f"CUSTOM DOMAIN SETUP REQUIRED:{domain_section.replace('<h3>', '').replace('</h3>', '').replace('<ol>', '').replace('</ol>', '').replace('<li>', '- ').replace('</li>', '').replace('<code>', '').replace('</code>', '').replace('<p>', '').replace('</p>', '').replace('<strong>', '').replace('</strong>', '')}" if custom_domain else ""}

{f"Impersonate for Testing:{impersonate_section.replace('<h3>', '').replace('</h3>', '').replace('<code>', '').replace('</code>', '').replace('<p>', '').replace('</p>', '').replace('<br>', '\n').replace('<strong>', '').replace('</strong>', '')}" if impersonate_section else ""}
        """

        msg = Message(
            subject=subject,
            recipients=[admin_email],
            html=html_body,
            body=text_body,
            sender=current_app.config.get('MAIL_SENDER', 'noreply@mail.bentcrankshaft.com')
        )

        mail.send(msg)
        print(f"✅ Admin notification sent to {admin_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send admin notification: {str(e)}")
        return False


def send_welcome_email(dealer_name, dealer_email, username, dealer_slug=None, temp_password=None, custom_domain=None):
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

        # Custom domain section
        custom_domain_section = ""
        if custom_domain:
            custom_domain_section = f"""
            <h3>Custom Domain Setup 🌐</h3>
            <p>You've chosen to use your own domain: <strong>{custom_domain}</strong></p>
            <p>To activate it, please point your domain DNS to our servers using one of these methods:</p>
            <div style="background: #f9f9f9; padding: 15px; border-left: 4px solid #2563EB; margin: 15px 0; border-radius: 3px;">
                <p><strong>Option 1 (Recommended): CNAME Record</strong></p>
                <p>If your domain registrar supports CNAME records:</p>
                <code style="background: #fff; padding: 8px; border-radius: 3px; display: block; margin: 10px 0; font-family: monospace;">
                Host: (leave blank or @)<br>
                Type: CNAME<br>
                Value: bentcrankshaft.com
                </code>
            </div>
            <div style="background: #f9f9f9; padding: 15px; border-left: 4px solid #2563EB; margin: 15px 0; border-radius: 3px;">
                <p><strong>Option 2: A Record</strong></p>
                <p>If CNAME is not available, ask our support team for the server IP address:</p>
                <code style="background: #fff; padding: 8px; border-radius: 3px; display: block; margin: 10px 0; font-family: monospace;">
                Host: (leave blank or @)<br>
                Type: A<br>
                Value: (contact support for IP)
                </code>
            </div>
            <p><strong>After updating DNS:</strong></p>
            <ol>
                <li>DNS changes can take 15-48 hours to propagate worldwide</li>
                <li>You'll receive a confirmation email once we detect your domain is properly configured</li>
                <li>Once active, your site will be available at https://{custom_domain}</li>
            </ol>
            <p style="color: #666; font-size: 13px;">
                <strong>Need help with DNS?</strong> Contact {support_email} and we'll assist you.
            </p>
            """

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

                    <h3>Your Website Address</h3>
                    <p>Your site is immediately available at:</p>
                    <p style="font-size: 16px;"><strong><a href="{login_url}">{login_url}</a></strong></p>
                    {custom_domain_section}

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
                        {f'<li><strong>Configure your domain</strong> - Follow the DNS instructions above</li>' if custom_domain else ''}
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
