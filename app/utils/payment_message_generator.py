def generate_simple_payment_message(
    user_name: str,
    project_name: str,
    project_price: float,
    tax_amount: float,
    final_amount: float,
    order_number: str,
    payment_type: str,
    payment_status: str,
    payment_date: str,
    language: str | None = None,
) -> str:
    """
    Generate a simple payment notification message without template.

    Args:
        user_name: Name of the user
        project_name: Name of the project/content
        project_price: Original amount
        tax_amount: Tax amount
        final_amount: Final total amount
        order_number: Order/invoice number
        payment_type: Type of payment method
        payment_status: Status of the payment
        payment_date: Date of the payment
        language: Language preference ("zh" for Chinese, else English)

    Returns:
        Formatted message content string
    """

    # Create simple text message content
    if language == "zh":
        if payment_status == "success":
            message_content = f"""🎉 支付成功通知

亲爱的 {user_name}，

恭喜！您的支付已成功处理。

订单信息：
订单号：{order_number}
内容：{project_name}
原始金额：${project_price:.2f}
税费：${tax_amount:.2f}
最终金额：${final_amount:.2f}
支付方式：{payment_type}
日期：{payment_date}

您的发票已作为附件发送。如有疑问，请联系我们的客服团队。

感谢您的购买！

---
这是一封自动邮件，请勿直接回复。"""
        elif payment_status == "failed":
            message_content = f"""❌ 支付失败通知

亲爱的 {user_name}，

很抱歉，您的支付未能成功处理。

订单信息：
订单号：{order_number}
内容：{project_name}
金额：${project_price:.2f}
日期：{payment_date}

请检查您的支付方式并重新尝试，或联系我们的客服团队获取帮助。

感谢您的理解。

---
这是一封自动邮件，请勿直接回复。"""
        elif payment_status == "cancelled":
            message_content = f"""⚠️ 支付取消通知

亲爱的 {user_name}，

您的支付已被取消。

订单信息：
订单号：{order_number}
内容：{project_name}
金额：${project_price:.2f}
日期：{payment_date}

如果这是意外操作，您可以随时重新完成购买。您的购物车已为您保存。

感谢您的关注。

---
这是一封自动邮件，请勿直接回复。"""
        else:
            message_content = f"""📧 支付状态通知

亲爱的 {user_name}，

您的订单状态已更新。

订单信息：
订单号：{order_number}
内容：{project_name}
状态：{payment_status}
金额：${project_price:.2f}
日期：{payment_date}

如有疑问，请联系我们的客服团队。

---
这是一封自动邮件，请勿直接回复。"""
    else:
        # English messages
        if payment_status == "success":
            message_content = f"""🎉 Payment Successful Notification

Dear {user_name},

Congratulations! Your payment has been processed successfully.

Order Information:
Order Number: {order_number}
Content: {project_name}
Original Amount: ${project_price:.2f}
Tax: ${tax_amount:.2f}
Final Amount: ${final_amount:.2f}
Payment Method: {payment_type}
Date: {payment_date}

Your invoice has been sent as an attachment. If you have any questions, please contact our support team.

Thank you for your purchase!

---
This is an automated email. Please do not reply directly."""
        elif payment_status == "failed":
            message_content = f"""❌ Payment Failed Notification

Dear {user_name},

We're sorry, but your payment could not be processed successfully.

Order Information:
Order Number: {order_number}
Content: {project_name}
Amount: ${project_price:.2f}
Date: {payment_date}

Please check your payment method and try again, or contact our support team for assistance.

Thank you for your understanding.

---
This is an automated email. Please do not reply directly."""
        elif payment_status == "cancelled":
            message_content = f"""⚠️ Payment Cancelled Notification

Dear {user_name},

Your payment has been cancelled.

Order Information:
Order Number: {order_number}
Content: {project_name}
Amount: ${project_price:.2f}
Date: {payment_date}

If this was unintentional, you can complete your purchase anytime. Your cart is saved for your convenience.

Thank you for your interest.

---
This is an automated email. Please do not reply directly."""
        else:
            message_content = f"""📧 Payment Status Notification

Dear {user_name},

Your order status has been updated.

Order Information:
Order Number: {order_number}
Content: {project_name}
Status: {payment_status}
Amount: ${project_price:.2f}
Date: {payment_date}

If you have any questions, please contact our support team.

---
This is an automated email. Please do not reply directly."""

    # Return the message content for use in other contexts
    return message_content
