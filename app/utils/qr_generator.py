import base64
import qrcode
from io import BytesIO
from app.utils.encrypt_data import AESJsonCipher


def generate_qr_code_from_encrypted_data(
    user_name: str,
    user_email: str,
    project_name: str,
    project_price: float,
    tax_amount: float,
    final_amount: float,
    order_number: str,
    payment_type: str,
    payment_date: str,
    secret_key: bytes,
) -> str:
    """
    生成包含加密用户信息的二维码，返回base64编码的图片数据

    Args:
        user_name: 用户名
        user_email: 用户邮箱
        project_name: 项目名称
        project_price: 原始金额
        tax_amount: 税费金额
        final_amount: 最终金额
        order_number: 订单号
        payment_type: 支付方式
        payment_date: 支付日期
        secret_key: 加密密钥

    Returns:
        base64编码的PNG图片数据
    """
    try:
        # 准备要加密的数据，确保所有数据都是JSON可序列化的
        data_to_encrypt = {
            "user_name": str(user_name),
            "user_email": str(user_email),
            "project_name": str(project_name),
            "project_price": float(project_price),
            "tax_amount": float(tax_amount),
            "final_amount": float(final_amount),
            "order_number": str(order_number),
            "payment_type": str(payment_type),
            "payment_date": str(payment_date),
        }

        # 使用AES加密数据
        cipher = AESJsonCipher(secret_key)
        encrypted_string = cipher.encrypt(data_to_encrypt)

        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(encrypted_string)
        qr.make(fit=True)

        # 创建二维码图片
        img = qr.make_image(fill_color="black", back_color="white")

        # 转换为base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_data = buffer.getvalue()
        buffer.close()

        # 返回base64编码的图片数据
        return base64.b64encode(img_data).decode("utf-8")

    except Exception as e:
        # 如果生成失败，返回一个默认的占位符图片或空字符串
        print(f"Error generating QR code: {e}")
        return ""


def decrypt_qr_code_data(encrypted_string: str, secret_key: bytes) -> dict:
    """
    解密二维码中的加密数据

    Args:
        encrypted_string: 加密的字符串
        secret_key: 解密密钥

    Returns:
        解密后的数据字典
    """
    try:
        cipher = AESJsonCipher(secret_key)
        return cipher.decrypt(encrypted_string)
    except Exception as e:
        print(f"Error decrypting QR code data: {e}")
        return {}
