"""
Email sending utilities for the application.
"""

from flask import render_template_string, current_app
from flask_mail import Mail, Message
from app.core.extensions import mail

def send_dealer_admin_notification(dealer_name, dealer_slug, custom_domain=None):
    """
    Send a notification to SaaS admin (ken@bentcrankshaft.com) with dealer setup details.

    Args:
        dealer_name (str): Name of the dealer
        dealer_slug (str): Dealer subdomain slug
        custom_domain (str, optional): Custom domain if provided
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

        # Note: SaaS admins don't need credentials - they have access to all dealers via impersonation feature

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
        support_email = "customerservice@bentcrankshaft.com"
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


def send_invoice_email(invoice, recipient_email, org):
    """
    Emails a formatted copy of an invoice to a customer.

    Args:
        invoice: Invoice instance (with line_items loaded)
        recipient_email (str): Where to send it
        org: Organization instance (for branding)
    """
    try:
        theme = org.theme_config or {}
        # Images are referenced as hosted URLs on the dealer's own subdomain -
        # NOT attached. Attached images (a QR code especially) trip Gmail's
        # "content presents a potential security issue" filter.
        base_url = f"https://{org.slug}.bentcrankshaft.com" if org.slug else ""
        logo_url = theme.get('logo_url')
        if logo_url and logo_url.startswith('/'):
            logo_full_url = base_url + logo_url
        else:
            logo_full_url = logo_url

        # Emails are relayed through the master Mailgun account for deliverability, but each
        # dealer's own contact email is set as Reply-To so customer replies land with the
        # dealer, not with the SaaS operator. Falls back to the shared sender if a dealer
        # hasn't set a contact email yet.
        base_sender = current_app.config.get('MAIL_SENDER', 'noreply@mail.bentcrankshaft.com')
        dealer_reply_to = theme.get('contact_email') or base_sender

        status_label = {'paid': 'PAID', 'void': 'VOID'}.get(invoice.status, 'UNPAID')
        status_color = {'paid': '#16a34a', 'void': '#6b7280'}.get(invoice.status, '#d97706')

        line_rows_html = ''.join(
            f"""<tr>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;">{li.description}</td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right;">{li.quantity}</td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right;">${li.unit_price:.2f}</td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right;">${li.line_total:.2f}</td>
            </tr>"""
            for li in invoice.line_items
        )
        line_rows_text = '\n'.join(
            f"  {li.quantity}x {li.description} @ ${li.unit_price:.2f} = ${li.line_total:.2f}"
            for li in invoice.line_items
        )

        # Dealer-configured payment buttons / QR codes / notes.
        pay_opts = [
            o for o in (org.invoice_payment_options or [])
            if invoice.status != 'void' and (invoice.status != 'paid' or o.always_show)
        ]
        pay_html, pay_text = '', ''
        if pay_opts:
            blocks = []
            for o in pay_opts:
                if o.kind == 'link' and o.url:
                    blocks.append(
                        f'<a href="{o.url}" style="display:inline-block;background:#2563eb;color:#fff;'
                        f'text-decoration:none;padding:10px 18px;border-radius:6px;font-weight:bold;">{o.label}</a>')
                elif o.kind == 'qr' and o.image_url:
                    # Hosted image (dealer subdomain), not an attachment.
                    src = o.image_url if o.image_url.startswith('http') else base_url + o.image_url
                    # Also show the target as a link so there's a working path if the image is blocked.
                    caption = (f'<div style="font-size:11px;"><a href="{o.url}">{o.url}</a></div>'
                               if o.url else '')
                    blocks.append(
                        f'<div style="display:inline-block;text-align:center;margin-right:16px;vertical-align:top;">'
                        f'<div style="font-weight:bold;font-size:13px;">{o.label}</div>'
                        f'<img src="{src}" alt="{o.label}" width="130" height="130" style="width:130px;height:130px;">'
                        f'{caption}</div>')
                elif o.kind == 'text' and o.body_text:
                    body = o.body_text.replace('\n', '<br>')
                    blocks.append(f'<div style="margin:6px 0;"><strong>{o.label}</strong><br>{body}</div>')
            pay_html = (
                '<div style="margin:24px 0;padding-top:16px;border-top:1px solid #ddd;">'
                '<div style="color:#666;font-weight:bold;margin-bottom:10px;">Payment Options</div>'
                + ' '.join(blocks) + '</div>')
            pay_text = "\n\nPayment Options:\n" + "\n".join(
                f"  {o.label}: {o.url or o.body_text or 'see QR code'}" for o in pay_opts)

        # Service invoices carry the ticket's work-notes log.
        notes_html, notes_text = '', ''
        st = getattr(invoice, 'service_ticket', None)
        if st is not None and getattr(st, 'notes', None):
            ordered = sorted(st.notes, key=lambda n: n.created_at)
            rows = ''.join(
                f'<div style="margin-bottom:8px;"><div style="color:#888;font-size:12px;">'
                f'{n.created_at.strftime("%b %d, %Y %I:%M %p")}</div>'
                f'<div>{(n.body or "").replace(chr(10), "<br>")}</div></div>'
                for n in ordered)
            notes_html = (
                '<div style="margin:24px 0;padding-top:16px;border-top:1px solid #ddd;">'
                '<div style="color:#666;font-weight:bold;margin-bottom:10px;">Work Notes</div>'
                + rows + '</div>')
            notes_text = "\n\nWork Notes:\n" + "\n".join(
                f"  [{n.created_at.strftime('%b %d, %Y %I:%M %p')}] {n.body or ''}" for n in ordered)

        subject = f"Invoice #{invoice.invoice_number} from {org.name}"

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 650px; margin: 0 auto; padding: 20px;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:20px;">
                        <div>
                            {f'<img src="{logo_full_url}" style="max-height:50px;"><br>' if logo_full_url else ''}
                            <strong style="font-size:18px;">{org.name}</strong>
                        </div>
                        <div style="text-align:right;">
                            <h2 style="margin:0;">INVOICE</h2>
                            <div style="color:#666;">#{invoice.invoice_number}</div>
                            <div style="color:#666;">{invoice.created_at.strftime('%B %d, %Y')}</div>
                            <span style="display:inline-block;margin-top:6px;padding:2px 10px;border-radius:4px;background:{status_color};color:#fff;font-size:12px;font-weight:bold;">{status_label}</span>
                        </div>
                    </div>

                    <p>Hi {invoice.bill_to_name or 'there'},</p>
                    <p>{"Thank you for your payment! Here's a copy of your paid invoice." if invoice.status == 'paid' else "Please find your invoice details below."}</p>

                    <table style="width:100%; border-collapse:collapse; margin:20px 0;">
                        <thead>
                            <tr style="background:#f9fafb;">
                                <th style="padding:8px;text-align:left;border-bottom:2px solid #e5e7eb;">Description</th>
                                <th style="padding:8px;text-align:right;border-bottom:2px solid #e5e7eb;">Qty</th>
                                <th style="padding:8px;text-align:right;border-bottom:2px solid #e5e7eb;">Price</th>
                                <th style="padding:8px;text-align:right;border-bottom:2px solid #e5e7eb;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {line_rows_html}
                        </tbody>
                    </table>

                    <div style="text-align:right; margin-bottom:20px;">
                        <div>Subtotal: ${invoice.subtotal:.2f}</div>
                        <div>Tax ({invoice.tax_rate}%): ${invoice.tax_amount:.2f}</div>
                        <div style="font-size:18px; font-weight:bold; margin-top:6px;">Total: ${invoice.total:.2f}</div>
                    </div>

                    {notes_html}
                    {pay_html}

                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                    <p style="color: #666; font-size: 12px;">
                        This is an automated email from {org.name}. Please contact us directly with any questions.
                    </p>
                </div>
            </body>
        </html>
        """

        text_body = f"""
Invoice #{invoice.invoice_number} from {org.name}
{invoice.created_at.strftime('%B %d, %Y')} - {status_label}

Bill To: {invoice.bill_to_name or ''}

Items:
{line_rows_text}

Subtotal: ${invoice.subtotal:.2f}
Tax ({invoice.tax_rate}%): ${invoice.tax_amount:.2f}
Total: ${invoice.total:.2f}{notes_text}{pay_text}

This is an automated email from {org.name}.
        """

        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            html=html_body,
            body=text_body,
            sender=(org.name, base_sender),
            reply_to=dealer_reply_to,
        )
        mail.send(msg)
        print(f"✅ Invoice #{invoice.invoice_number} emailed to {recipient_email} (reply-to: {dealer_reply_to})")
        return True

    except Exception as e:
        print(f"❌ Failed to email invoice #{invoice.invoice_number} to {recipient_email}: {str(e)}")
        return False
