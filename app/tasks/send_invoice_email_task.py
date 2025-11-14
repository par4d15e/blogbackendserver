import asyncio
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from app.core.logger import logger_manager
from app.core.celery import celery_app, with_db_init
from app.utils.email import email_service
from app.utils.pdf_generator import generate_invoice_pdf
from app.utils.payment_message_generator import generate_simple_payment_message
from app.core.config.settings import settings


async def _send_simple_text_email(
    email_service,
    subject: str,
    recipient: str,
    message_content: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """Send a simple text email with the given message content and optional attachments."""
    from app.utils.email import EmailMessage

    email_message = EmailMessage(
        subject=subject,
        recipient=recipient,
        sender=email_service.settings.email.EMAIL_HOST_USER,
    ).set_text_content(message_content)

    # Add attachments if provided
    if attachments:
        for attachment in attachments:
            email_message.add_attachment(
                filename=attachment["filename"],
                content=attachment["content"],
                content_type=attachment.get("content_type", "application/octet-stream"),
            )

    mime_message = email_message.build()
    await email_service.backend.send_email(mime_message)


@celery_app.task(
    name="send_invoice_email_task", bind=True, max_retries=3, default_retry_delay=30
)
@with_db_init
def send_invoice_email_task(
    self,
    user_email: str,
    user_name: str,
    project_section_name: str,
    project_name: str,
    project_price: float,
    tax_amount: float,
    final_amount: float,
    order_number: str,
    payment_type: str,
    payment_status: str,
    payment_date: str,
    language: str | None = None,
) -> None:
    """Send invoice email task"""
    try:
        logger = logger_manager.get_logger(__name__)
        logger.info("Send invoice email task")

        # Determine email subject and template based on payment status
        attachments = []

        # Get company name from settings
        company_name = getattr(settings.invoice, "COMPANY_NAME", "HeyXiaoli")
        company_phone = getattr(settings.invoice, "COMPANY_PHONE", "1234567890")
        company_email = getattr(
            settings.invoice, "COMPANY_EMAIL", "hello@heyxiaoli.com"
        )

        if payment_status == "success":
            # Success: Send invoice with PDF attachment
            if language == "zh":
                subject = f"[{settings.app.APP_NAME}] - 📄 发票 - 支付成功"
            else:
                subject = f"[{settings.app.APP_NAME}] - 📄 Invoice - Payment Successful"

            # Generate PDF invoice for successful payments
            try:
                logger.info("Generating PDF invoice for successful payment...")
                pdf_bytes = generate_invoice_pdf(
                    user_name=user_name,
                    user_email=user_email,
                    project_section_name=project_section_name,
                    project_name=project_name,
                    project_price=project_price,
                    tax_amount=tax_amount,
                    final_amount=final_amount,
                    order_number=order_number,
                    payment_type=payment_type,
                    payment_date=payment_date,
                    language=language,
                    company_name=company_name,
                    company_phone=company_phone,
                    company_email=company_email,
                )

                # Create filename based on order number and language
                if language == "zh":
                    pdf_filename = f"发票_{order_number}.pdf"
                else:
                    pdf_filename = f"invoice_{order_number}.pdf"

                attachments.append(
                    {
                        "filename": pdf_filename,
                        "content": pdf_bytes,
                        "content_type": "application/pdf",
                    }
                )

                logger.info(f"PDF invoice generated successfully: {pdf_filename}")

            except Exception as pdf_error:
                logger.error(f"Failed to generate PDF invoice: {pdf_error}")
                # Continue without PDF attachment if generation fails

        elif payment_status == "failed":
            # Failed: Send notification message only
            if language == "zh":
                subject = f"[{settings.app.APP_NAME}] - ❌ 支付失败通知"
            else:
                subject = f"[{settings.app.APP_NAME}] - ❌ Payment Failed Notification"
            logger.info("Sending payment failed notification (no PDF)")

        elif payment_status == "cancelled":
            # Cancelled: Send notification message only
            if language == "zh":
                subject = f"[{settings.app.APP_NAME}] - ⚠️ 支付取消通知"
            else:
                subject = (
                    f"[{settings.app.APP_NAME}] - ⚠️ Payment Cancelled Notification"
                )
            logger.info("Sending payment cancelled notification (no PDF)")

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment status",
            )

        # 在Celery任务环境中运行异步发送
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Send different types of emails based on payment status
        if payment_status == "success":
            # Success: Generate simple text message and send with PDF attachment
            try:
                # Generate the simple text message content (but don't send email yet)
                message_content = generate_simple_payment_message(
                    user_name=str(user_name),
                    project_name=str(project_name),
                    project_price=float(project_price),
                    tax_amount=float(tax_amount),
                    final_amount=float(final_amount),
                    order_number=str(order_number),
                    payment_type=str(payment_type),
                    payment_status=str(payment_status),
                    payment_date=str(payment_date),
                    language=language,
                )

                # Send email with simple text content and PDF attachment
                loop.run_until_complete(
                    _send_simple_text_email(
                        email_service=email_service,
                        subject=subject,
                        recipient=user_email,
                        message_content=message_content,
                        attachments=attachments if attachments else None,
                    )
                )

                logger.info(
                    f"Success email sent with simple text and PDF attachment to {user_email}"
                )

            except Exception as e:
                logger.error(f"Failed to send success email: {e}")
                # Fallback to simple text email if sending fails
                logger.info("Falling back to simple text email")
                message_content = generate_simple_payment_message(
                    user_name=str(user_name),
                    project_name=str(project_name),
                    project_price=float(project_price),
                    tax_amount=float(tax_amount),
                    final_amount=float(final_amount),
                    order_number=str(order_number),
                    payment_type=str(payment_type),
                    payment_status=str(payment_status),
                    payment_date=str(payment_date),
                    language=language,
                )
        else:
            # Failed/Cancelled: Send simple text message
            message_content = generate_simple_payment_message(
                user_name=str(user_name),
                project_name=str(project_name),
                project_price=float(project_price),
                tax_amount=float(tax_amount),
                final_amount=float(final_amount),
                order_number=str(order_number),
                payment_type=str(payment_type),
                payment_status=str(payment_status),
                payment_date=str(payment_date),
                language=language,
            )

            loop.run_until_complete(
                _send_simple_text_email(
                    email_service=email_service,
                    subject=subject,
                    recipient=user_email,
                    message_content=message_content,
                )
            )

    except Exception as e:
        logger.error(f"Send invoice email task failed: {e}")
        raise self.retry(exc=e)
