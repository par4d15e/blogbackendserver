from pathlib import Path
from typing import Optional, Union
from datetime import datetime
from app.core.i18n.i18n import Language
import weasyprint
from weasyprint.text.fonts import FontConfiguration
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound

from app.core.logger import logger_manager
from app.utils.qr_generator import generate_qr_code_from_encrypted_data


class InvoicePDFGenerator:
    """Invoice PDF generator using WeasyPrint and Jinja2 templates."""

    def __init__(self, template_dir: Union[str, Path] = "static/templete"):
        self.template_dir = Path(template_dir)
        self.logger = logger_manager.get_logger(__name__)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # 设置字体目录路径
        self.font_dir = self.template_dir.parent / "font"
        self.logger.info(f"Font directory: {self.font_dir}")

    def _select_template_name(
        self, base_template: str, language_code: Optional[str]
    ) -> str:
        """Select a language-specific template with graceful fallback."""
        if language_code:
            candidates = [
                f"{language_code}/{base_template}",
                f"{base_template}_{language_code}",
                base_template,
            ]
        else:
            candidates = [base_template]

        for candidate in candidates:
            template_path = self.template_dir / f"{candidate}.html"
            if template_path.exists():
                if candidate != base_template:
                    self.logger.info(
                        f"Using language-specific template: '{candidate}.html'"
                    )
                return candidate

        return base_template

    def render_invoice_html(
        self,
        user_name: str,
        user_email: str,
        project_section_name: str,
        project_name: str,
        project_price: float,
        tax_amount: float,
        final_amount: float,
        order_number: str,
        payment_type: str,
        payment_date: str,
        language: Union[Language, str],
        company_name: str = "HeyXiaoli",
        company_phone: str = "1234567890",
        company_email: str = "hello@heyxiaoli.com",
    ) -> str:
        """Render invoice HTML with PDF-optimized styles."""
        try:
            # Normalize language and select template
            if isinstance(language, str):
                language_code = language
            else:
                language_code = language.value
            template_name = self._select_template_name("invoice", language_code)

            # Get template
            template = self.env.get_template(f"{template_name}.html")

            # Prepare context - ensure numeric values are properly typed
            context = {
                "user_name": str(user_name),
                "user_email": str(user_email),
                "project_section_name": str(project_section_name),
                "project_name": str(project_name),
                "project_price": float(project_price),
                "tax_amount": float(tax_amount),
                "final_amount": float(final_amount),
                "order_number": str(order_number),
                "payment_type": str(payment_type),
                "payment_date": str(payment_date),
                "company_name": str(company_name),
                "company_phone": str(company_phone),
                "company_email": str(company_email),
                "pdf_generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_pdf_version": True,
            }

            # Generate QR code with encrypted data
            try:
                # 使用一个固定的密钥（在实际生产环境中应该从配置中获取）
                secret_key = b"HeyXiaoliSecret16"[:16]  # 确保是16字节
                qr_code_base64 = generate_qr_code_from_encrypted_data(
                    user_name=user_name,
                    user_email=user_email,
                    project_name=project_name,
                    project_price=project_price,
                    tax_amount=tax_amount,
                    final_amount=final_amount,
                    order_number=order_number,
                    payment_type=payment_type,
                    payment_date=payment_date,
                    secret_key=secret_key,
                )

                # 确保二维码数据不为空且格式正确
                if qr_code_base64 and len(qr_code_base64) > 100:  # 基本的base64长度检查
                    context["qr_code_base64"] = qr_code_base64
                    self.logger.info("QR code generated successfully")
                else:
                    self.logger.warning(
                        "QR code generation failed or returned empty data"
                    )
                    context["qr_code_base64"] = ""

            except Exception as e:
                self.logger.warning(f"Failed to generate QR code: {e}")
                context["qr_code_base64"] = ""

            # Render template
            html_content = template.render(**context)

            # Return the original HTML template without any modifications
            # WeasyPrint will use the template's native styles including @media print
            return html_content

        except TemplateNotFound:
            self.logger.error(
                f"Template '{template_name}' not found in '{self.template_dir}'"
            )
            raise FileNotFoundError(
                f"Template '{template_name}' not found in '{self.template_dir}'"
            )
        except Exception as e:
            self.logger.error(f"Error rendering invoice template: {e}")
            raise ValueError(f"Failed to render invoice template: {str(e)}")

    def generate_invoice_pdf(
        self,
        user_name: str,
        user_email: str,
        project_section_name: str,
        project_name: str,
        project_price: float,
        tax_amount: float,
        final_amount: float,
        order_number: str,
        payment_type: str,
        payment_date: str,
        language: Optional[Union[str, Language]] = None,
        company_name: str = "HeyXiaoli",
        company_phone: str = "1234567890",
        company_email: str = "hello@heyxiaoli.com",
        output_path: Optional[Union[str, Path]] = None,
    ) -> Union[bytes, Path]:
        """Generate invoice PDF from template data."""
        # 确保 language 有默认值
        if language is None:
            language = Language.ZH_CN
        try:
            # Render HTML content
            html_content = self.render_invoice_html(
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

            # Generate PDF using WeasyPrint
            html_doc = weasyprint.HTML(
                string=html_content, base_url=str(self.template_dir), encoding="utf-8"
            )

            # 配置字体嵌入选项
            font_config = FontConfiguration()

            # 配置PDF选项，使用PDF 1.7版本以确保更好的兼容性
            pdf_options = {
                "font_config": font_config,
                "pdf_version": "1.7",  # 使用PDF 1.7版本，支持更多现代特性
                "optimize_images": True,  # 优化图片
                "jpeg_quality": 95,  # JPEG质量
                "presentational_hints": True,  # 保持CSS表现提示
            }

            if output_path:
                # Save to file
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                html_doc.write_pdf(str(output_path), **pdf_options)
                self.logger.info(f"Invoice PDF saved to: {output_path}")
                return output_path
            else:
                # Return bytes
                pdf_bytes = html_doc.write_pdf(**pdf_options)
                self.logger.info(
                    f"Invoice PDF generated successfully for order: {order_number}"
                )
                return pdf_bytes

        except Exception as e:
            self.logger.error(f"Error generating invoice PDF: {e}")
            raise RuntimeError(f"Failed to generate invoice PDF: {str(e)}")


# Global instance
_pdf_generator = None


def get_invoice_pdf_generator() -> InvoicePDFGenerator:
    """Get the global invoice PDF generator instance."""
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = InvoicePDFGenerator("static/templete")
    return _pdf_generator


# Convenience function
def generate_invoice_pdf(
    user_name: str,
    user_email: str,
    project_section_name: str,
    project_name: str,
    project_price: float,
    tax_amount: float,
    final_amount: float,
    order_number: str,
    payment_type: str,
    payment_date: str,
    language: Optional[Union[str, Language]] = None,
    company_name: str = "HeyXiaoli",
    company_phone: str = "1234567890",
    company_email: str = "hello@heyxiaoli.com",
    output_path: Optional[Union[str, Path]] = None,
) -> Union[bytes, Path]:
    """Convenience function to generate invoice PDF."""
    generator = get_invoice_pdf_generator()
    return generator.generate_invoice_pdf(
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
        output_path=output_path,
    )
