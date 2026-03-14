from config.env import env


rest_password_url = env("REST_PASSWORD_URL")
current_site = "emily.sa"


def create_otp_template(user_name, OTP, user_email):
    otp_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8" />
    <title></title>
    <style>
        body {{
        margin: 0;
        padding: 0;
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        color: #333;
        background-color: #fff;
        }}

        .container {{
        margin: 0 auto;
        width: 100%;
        max-width: 600px;
        padding: 0 0px;
        padding-bottom: 10px;
        border-radius: 5px;
        line-height: 1.8;
        }}
        .header {{
        border-bottom: 1px solid #eee;
        }}
        .header a {{
        font-size: 1.4em;
        color: #000;
        text-decoration: none;
        font-weight: 600;
        }}

        .content {{
        min-width: 700px;
        overflow: auto;
        line-height: 2;
        }}

        .otp {{
        background: linear-gradient(to right, #00bc69 0, #00bc88 50%, #00bca8 100%);
        margin: 0 auto;
        width: max-content;
        padding: 0 10px;
        color: #fff;
        border-radius: 4px;
        }}

        .footer {{
        color: #aaa;
        font-size: 0.8em;
        line-height: 1;
        font-weight: 300;
        }}

        .email-info {{
        color: #666666;
        font-weight: 400;
        font-size: 13px;
        line-height: 18px;
        padding-bottom: 6px;
        }}

        .email-info a {{
        text-decoration: none;
        color: #00bc69;
        }}
    </style>
    </head>

    <body>
    <!--Subject: Login Verification Required for Your Emily Account-->
    <div class="container">
        <div class="header">
        <a>Emily.sa</a>
        </div>
        <br />
        <strong>Dear {user_name},</strong>
        <p>
        We have received a login request for your Emily.sa account. For
        security purposes, please verify your identity by providing the
        following One-Time Password (OTP).
        <br />
        <b>Your One-Time Password (OTP) verification code is:</b>
        </p>
        <h2 class="otp">{OTP}</h2>
        <p style="font-size: 0.9em">
        <strong>One-Time Password (OTP) is valid for 15 minutes.</strong>
        <br />
        <br />
        If you did not initiate this login request, please disregard this
        message. Please ensure the confidentiality of your OTP and do not share
        it with anyone.<br />
        <strong>Do not forward or give this code to anyone.</strong>
        <br />
        <br />
        <strong>Thank you for using Emily.sa.</strong>
        <br />
        <br />
        Best regards,
        <br />
        <strong>Emily.sa</strong>
        </p>

        <hr style="border: none; border-top: 0.5px solid #131111" />
        <div class="footer">
        <p>This email can't receive replies.</p>
        <p>
            For more information about Emily and your account, visit
            <strong>Emily.sa</strong>
        </p>
        </div>
    </div>
    <div style="text-align: center">
        <div class="email-info">
        <span>
            This email was sent to
            <a href="mailto:{user_email}">{user_email}</a>
        </span>
        </div>
        <div class="email-info">
        <a href="/">Emily.sa</a> | Saudi Arabia
        </div>
        <div class="email-info">
        &copy; 2024 Emily.sa  All rights
        reserved.
        </div>
    </div>
    </body>
    </html>
    """
    return otp_template


def create_password_reset_template(user_name, reset_link, operating_system, browser_name):

    # Create the image tag with inline styles and explicit dimensions
    logo_html = "Emily.sa"

    reset_template = f"""
		<!DOCTYPE html>
	<html>
	<head>
	<meta content="text/html; charset=UTF-8" http-equiv="Content-Type" />
	<title></title>
	<style>
			/* Base ------------------------------ */

			@import url("https://fonts.googleapis.com/css?family=Nunito+Sans:400,700&display=swap");

			body {{
				width: 100% !important;
				height: 100%;
				margin: 0;
				-webkit-text-size-adjust: none;
			}}

			a {{
				color: #3869D4;
			}}

			a img {{
				border: none;
			}}

			td {{
				word-break: break-word;
			}}

			.preheader {{
				display: none !important;
				visibility: hidden;
				mso-hide: all;
				font-size: 1px;
				line-height: 1px;
				max-height: 0;
				max-width: 0;
				opacity: 0;
				overflow: hidden;
			}}

			/* Type ------------------------------ */

			body,
			td,
			th {{
				font-family: "Nunito Sans", Helvetica, Arial, sans-serif;
			}}

			h1 {{
				margin-top: 0;
				color: #333333;
				font-size: 22px;
				font-weight: bold;
				text-align: left;
			}}

			h2 {{
				margin-top: 0;
				color: #333333;
				font-size: 16px;
				font-weight: bold;
				text-align: left;
			}}

			h3 {{
				margin-top: 0;
				color: #333333;
				font-size: 14px;
				font-weight: bold;
				text-align: left;
			}}

			td,
			th {{
				font-size: 16px;
			}}

			p,
			ul,
			ol,
			blockquote {{
				margin: .4em 0 1.1875em;
				font-size: 16px;
				line-height: 1.625;
			}}

			p.sub {{
				font-size: 13px;
			}}

			/* Utilities ------------------------------ */

			.align-right {{
				text-align: right;
			}}

			.align-left {{
				text-align: left;
			}}

			.align-center {{
				text-align: center;
			}}

			.u-margin-bottom-none {{
				margin-bottom: 0;
			}}

			/* Buttons ------------------------------ */

			.button {{
				display: inline-block;
				color: #FFF;
				text-decoration: none;
				border-radius: 4px;
				box-shadow: 0 2px 3px rgba(0, 0, 0, 0.16);
				-webkit-text-size-adjust: none;
				box-sizing: border-box;
				padding: 10px 18px;
			}}

			.button--green {{
				background: linear-gradient(to right, #00bc69 0, #00bc88 50%, #00bca8 100%) !important;
				color: #fff !important;
				border: none !important;
				margin: 0 auto !important;
				width: max-content !important;
			}}

			.button--red {{
				background-color: #FF6136;
				border-top: 10px solid #FF6136;
				border-right: 18px solid #FF6136;
				border-bottom: 10px solid #FF6136;
				border-left: 18px solid #FF6136;
			}}

			@media only screen and (max-width: 500px) {{
				.button {{
					width: 100% !important;
					text-align: center !important;
				}}
			}}

			/* Attribute list ------------------------------ */

			.attributes {{
				margin: 0 0 21px;
			}}

			.attributes_content {{
				background-color: #F4F4F7;
				padding: 16px;
			}}

			.attributes_item {{
				padding: 0;
			}}

			/* Related Items ------------------------------ */

			.related {{
				width: 100%;
				margin: 0;
				padding: 25px 0 0 0;
				-premailer-width: 100%;
				-premailer-cellpadding: 0;
				-premailer-cellspacing: 0;
			}}

			.related_item {{
				padding: 10px 0;
				color: #CBCCCF;
				font-size: 15px;
				line-height: 18px;
			}}

			.related_item-title {{
				display: block;
				margin: .5em 0 0;
			}}

			.related_item-thumb {{
				display: block;
				padding-bottom: 10px;
			}}

			.related_heading {{
				border-top: 1px solid #CBCCCF;
				text-align: center;
				padding: 25px 0 10px;
			}}

			/* Discount Code ------------------------------ */

			.discount {{
				width: 100%;
				margin: 0;
				padding: 24px;
				-premailer-width: 100%;
				-premailer-cellpadding: 0;
				-premailer-cellspacing: 0;
				background-color: #F4F4F7;
				border: 2px dashed #CBCCCF;
			}}

			.discount_heading {{
				text-align: center;
			}}

			.discount_body {{
				text-align: center;
				font-size: 15px;
			}}

			/* Social Icons ------------------------------ */

			.social {{
				width: auto;
			}}

			.social td {{
				padding: 0;
				width: auto;
			}}

			.social_icon {{
				height: 20px;
				margin: 0 8px 10px 8px;
				padding: 0;
			}}

			/* Data table ------------------------------ */

			.purchase {{
				width: 100%;
				margin: 0;
				padding: 35px 0;
				-premailer-width: 100%;
				-premailer-cellpadding: 0;
				-premailer-cellspacing: 0;
			}}

			.purchase_content {{
				width: 100%;
				margin: 0;
				padding: 25px 0 0 0;
				-premailer-width: 100%;
				-premailer-cellpadding: 0;
				-premailer-cellspacing: 0;
			}}

			.purchase_item {{
				padding: 10px 0;
				color: #51545E;
				font-size: 15px;
				line-height: 18px;
			}}

			.purchase_heading {{
				padding-bottom: 8px;
				border-bottom: 1px solid #EAEAEC;
			}}

			.purchase_heading p {{
				margin: 0;
				color: #85878E;
				font-size: 12px;
			}}

			.purchase_footer {{
				padding-top: 15px;
				border-top: 1px solid #EAEAEC;
			}}

			.purchase_total {{
				margin: 0;
				text-align: right;
				font-weight: bold;
				color: #333333;
			}}

			body {{
				background-color: #F2F4F6;
				color: #51545E;
			}}

			p {{
				color: #51545E;
			}}

			.email-wrapper {{
				width: 100%;
				margin: 0;
				padding: 0;
				-premailer-width: 100%;
				-premailer-cellpadding: 0;
				-premailer-cellspacing: 0;
				background-color: #F2F4F6;
			}}

			.email-content {{
				width: 100%;
				margin: 0;
				padding: 0;
				-premailer-width: 100%;
				-premailer-cellpadding: 0;
				-premailer-cellspacing: 0;
			}}

			/* Masthead ----------------------- */

			.email-masthead {{
				padding: 25px 0;
				text-align: center;
			}}

			.email-masthead_logo {{
				width: 94px;
			}}

			.email-masthead_name {{
				font-size: 16px;
				font-weight: bold;
				color: #A8AAAF;
				text-decoration: none;
				text-shadow: 0 1px 0 white;
			}}

			/* Body ------------------------------ */

			.email-body {{
				width: 100%;
				margin: 0;
				padding: 0;
				-premailer-width: 100%;
				-premailer-cellpadding: 0;
				-premailer-cellspacing: 0;
			}}

			.email-body_inner {{
				width: 570px;
				margin: 0 auto;
				padding: 0;
				-premailer-width: 570px;
				-premailer-cellpadding: 0;
				-premailer-cellspacing: 0;
				background-color: #FFFFFF;
			}}

			.email-footer {{
				width: 570px;
				margin: 0 auto;
				padding: 0;
				-premailer-width: 570px;
				-premailer-cellpadding: 0;
				-premailer-cellspacing: 0;
				text-align: center;
			}}

			.email-footer p {{
				color: #A8AAAF;
			}}

			.body-action {{
				width: 100%;
				margin: 30px auto;
				padding: 0;
				-premailer-width: 100%;
				-premailer-cellpadding: 0;
				-premailer-cellspacing: 0;
				text-align: center;
			}}

			.body-sub {{
				margin-top: 25px;
				padding-top: 25px;
				border-top: 1px solid #EAEAEC;
			}}

			.content-cell {{
				padding: 45px;
			}}

			/*Media Queries ------------------------------ */

			@media only screen and (max-width: 600px) {{
				.email-body_inner,
				.email-footer {{
					width: 100% !important;
				}}
			}}
	</style>
	<!--[if mso]>
	<style type="text/css">
		.f-fallback {{
		font-family: Arial, sans-serif;
		}}
	</style>
	<![endif]-->
	</head>
	<body>
	<span class="preheader">Use this link to reset your password. The link is only valid for 10 minuts.</span>
	<table cellpadding="0" cellspacing="0" class="email-wrapper" role="presentation" width="100%">
	<tr>
		<td align="center">
		<table cellpadding="0" cellspacing="0" class="email-content" role="presentation" width="100%">
			<tr>
			<td class="email-masthead" style="text-align: center;">
				<a class="f-fallback email-masthead_name" href="https://emily.sa/" target="_blank">
					{logo_html}
				</a>
			</td>
			</tr>
			<!-- Email Body -->
			<tr>
			<td cellpadding="0" cellspacing="0" class="email-body" width="570">
				<table align="center" cellpadding="0" cellspacing="0" class="email-body_inner" role="presentation"
					width="570">
				<!-- Body content -->
				<tr>
					<td class="content-cell">
					<div class="f-fallback">
						<h1>Hi {user_name},</h1>
						<p>You recently requested to reset your password for your Emily account. Use the button below to
						reset it. <strong>This password reset is only valid for the next 10 minuts.</strong></p>
						<!-- Action -->
						<table align="center" cellpadding="0" cellspacing="0" class="body-action" role="presentation"
							width="100%">
						<tr>
							<td align="center">
							<!-- Border based button
		https://litmus.com/blog/a-guide-to-bulletproof-buttons-in-email-design -->
							<table border="0" cellpadding="0" cellspacing="0" role="presentation" width="100%">
								<tr>
								<td align="center">
									<a class="f-fallback button button--green" href="{reset_link}" target="_blank">Reset your password</a>
								</td>
								</tr>
							</table>
							</td>
						</tr>
						</table>
						<p>For security, this request was received from a {operating_system} device using {browser_name}. If
						you did not request a password reset, please ignore this email or
						<a href="mailto:support@emily.sa">contact support</a>
						if you have questions.</p>
						<p>Thanks,
						<br>The Emily.sa team</p>
						<!-- Sub copy -->
						<table class="body-sub" role="presentation">
						<tr>
							<td>

							</td>
						</tr>
						</table>
					</div>
					</td>
				</tr>
				</table>
			</td>
			</tr>
			<tr>
			<td>
				<table align="center" cellpadding="0" cellspacing="0" class="email-footer" role="presentation" width="570">
				<tr>
					<td align="center" class="content-cell">
					<p class="f-fallback sub align-center">
						© 2024 Emily.sa All rights reserved.
						Emily.sa
						<br>Saudi Arabia.

					</p>
					</td>
				</tr>
				</table>
			</td>
			</tr>
		</table>
		</td>
	</tr>
	</table>
	</body>
	</html>
    """
    return reset_template
