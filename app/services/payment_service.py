import stripe
from typing import Any, Dict, List, Optional, Tuple
from fastapi import Depends, HTTPException, Request
from app.models.user_model import RoleType
from app.core.config.settings import settings
from app.core.logger import logger_manager
from app.crud.payment_crud import PaymentCrud, get_payment_crud
from app.models.payment_model import PaymentStatus, PaymentType
from app.core.i18n.i18n import Language, get_message, get_current_language
from app.tasks.send_invoice_email_task import send_invoice_email_task
from app.tasks import notification_task
from app.schemas.common import NotificationType


class PaymentService:
    def __init__(self, payment_crud: PaymentCrud):
        # 设置 Stripe API 密钥
        stripe.api_key = settings.stripe.STRIPE_SECRET_KEY.get_secret_value()
        self.payment_crud = payment_crud
        self.logger = logger_manager.get_logger(__name__)

    async def create_payment_intent(
        self,
        user_id: int,
        project_id: int,
        cover_url: str,
        project_name: str,
        project_description: str,
        project_price: float,
        tax_name: str,
        tax_rate: float,
        tax_amount: float,
        final_amount: float,
    ) -> Optional[str]:
        """创建 Stripe 支付意图"""
        try:
            response = await self.payment_crud.create_payment_intent(
                user_id=user_id,
                project_id=project_id,
                cover_url=cover_url,
                project_name=project_name,
                project_description=project_description,
                project_price=project_price,
                tax_name=tax_name,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                final_amount=final_amount,
                
            )

            self.logger.info(
                f"创建支付意图，金额: {response['final_amount']} 分，货币: NZD"
            )

            # 获取项目信息
            product = stripe.Product.create(
                name=response["project"]["project_name"],
                description=response["project"]["project_description"],
                images=[response["project"]["cover_url"]],
                metadata={
                    "project_id": str(response["project"]["project_id"]),
                    "user_id": str(response["user"]["user_id"]),
                },
            )

            stripe.Price.create(
                product=product.id,
                unit_amount=int(response["final_amount"] * 100),
                currency="nzd",
            )

            # 创建stripe 用户
            user_email = response["user"]["email"]
            user_name = response["user"]["user_name"]

            customers = stripe.Customer.list(email=user_email, limit=1)

            if customers.data:
                customer_id = customers.data[0].id
            else:
                customer_id = stripe.Customer.create(
                    email=user_email,
                    name=user_name,
                ).id

            # Stripe metadata 只接受字符串值，需要将嵌套对象扁平化
            metadata = {
                "user_id": str(response["user"]["user_id"]),
                "user_name": str(response["user"]["user_name"]),
                "user_email": str(response["user"]["email"]),
                "project_id": str(response["project"]["project_id"]),
                "cover_url": response["project"]["cover_url"],  # 添加封面URL
                "project_name": response["project"]["project_name"],  # 修正字段名
                "project_slug": response["project"]["project_slug"],
                "project_description": response["project"]["project_description"],
                "project_price": response["project"]["project_price"],
                # 添加 section 名称
                "project_section_name": response["project"].get(
                    "project_section_name", ""
                ),
                "tax_name": response["tax"]["tax_name"],
                "tax_rate": response["tax"]["tax_rate"],
                "tax_amount": response["tax"]["tax_amount"],
                "final_amount": response["final_amount"],
                "order_number": response["order_number"],
                "language": get_current_language().value,
            }

            # 使用正确的 Stripe API 调用方式
            intent = stripe.PaymentIntent.create(
                amount=int(response["final_amount"] * 100),
                currency="nzd",
                customer=customer_id,
                description=response["project"]["project_description"],
                metadata=metadata,
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "always",
                },
            )

            self.logger.info(f"支付意图创建成功，ID: {intent.id}")
            return intent.client_secret

        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe 支付意图创建失败: {str(e)}")
            raise HTTPException(
                status_code=400, detail=f"Payment creation failed: {str(e)}"
            )
        except Exception as e:
            self.logger.error(f"支付意图创建时发生未知错误: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Internal server error during payment creation"
            )

    def _get_payment_type_from_method(self, payment_method_id: str) -> PaymentType:
        """从支付方式ID获取支付类型"""
        if not payment_method_id:
            return PaymentType.card

        try:
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            payment_method_type = payment_method.get("type")

            payment_type_map = {
                PaymentType.card.name: PaymentType.card,
                PaymentType.link.name: PaymentType.link,
                PaymentType.klarna.name: PaymentType.klarna,
                PaymentType.afterpay_clearpay.name: PaymentType.afterpay_clearpay,
                PaymentType.alipay.name: PaymentType.alipay,
            }

            return payment_type_map.get(payment_method_type, PaymentType.card)
        except Exception as e:
            self.logger.warning(f"无法获取支付方式详情: {str(e)}")
            return PaymentType.card

    def _extract_payment_metadata(self, payment_intent) -> dict:
        """提取支付意图的元数据"""
        return {
            "user_id": payment_intent.metadata.get("user_id"),
            "user_name": payment_intent.metadata.get("user_name"),
            "user_email": payment_intent.metadata.get("user_email"),
            "project_id": payment_intent.metadata.get("project_id"),
            "cover_url": payment_intent.metadata.get("cover_url"),  # 添加封面URL
            "project_name": payment_intent.metadata.get("project_name"),
            "project_slug": payment_intent.metadata.get("project_slug"),
            "project_description": payment_intent.metadata.get("project_description"),
            "project_price": payment_intent.metadata.get("project_price"),
            # 添加 section 名称
            "project_section_name": payment_intent.metadata.get("project_section_name"),
            "tax_name": payment_intent.metadata.get("tax_name"),
            "tax_rate": payment_intent.metadata.get("tax_rate"),
            "tax_amount": payment_intent.metadata.get("tax_amount"),
            "final_amount": payment_intent.metadata.get("final_amount"),
            "order_number": payment_intent.metadata.get("order_number"),
            "language": payment_intent.metadata.get("language"),
        }

    def _validate_metadata(self, metadata: dict) -> bool:
        """验证元数据是否完整"""
        required_fields = [
            "user_id",
            "user_name",
            "user_email",
            "project_id",
            "project_slug",
            "cover_url",
            "project_name",
            "project_description",
            "project_price",
            "tax_name",
            "tax_rate",
            "tax_amount",
            "final_amount",
            "order_number",
            "language",
        ]

        for field in required_fields:
            if not metadata.get(field):
                self.logger.error(f"支付回调事件中缺少必要的元数据: {field}")
                return False
        return True

    async def _process_payment_event(
        self, payment_intent, payment_status: PaymentStatus, status_name: str
    ):
        """处理支付事件的通用逻辑"""
        # 获取支付类型
        payment_type = self._get_payment_type_from_method(
            payment_intent.get("payment_method")
        )

        # 提取元数据
        metadata = self._extract_payment_metadata(payment_intent)

        # 验证元数据
        if not self._validate_metadata(metadata):
            return {"status": "error", "message": "Missing required metadata"}
        # 记录日志
        self.logger.info(
            f"Final payment_type value: {payment_type} (type: {type(payment_type)})"
        )

        # 创建支付记录
        payment_record = await self.payment_crud.create_payment_record(
            user_id=int(metadata["user_id"]),
            project_id=int(metadata["project_id"]),
            order_number=metadata["order_number"],
            payment_type=payment_type,
            final_amount=metadata["final_amount"],
            tax_name=metadata["tax_name"],
            tax_rate=metadata["tax_rate"],
            tax_amount=metadata["tax_amount"],
            payment_status=payment_status,
        )

        # 发送通知（仅在支付成功时发送）
        if payment_status == PaymentStatus.success:
            try:
                self.logger.info(
                    f"支付成功，Stripe 将自动发送收据到: {metadata['user_email']}"
                )

                # 发送自定义发票邮件
                send_invoice_email_task.delay(
                    user_email=metadata["user_email"],
                    user_name=metadata["user_name"],
                    project_section_name=metadata.get(
                        "project_section_name", ""),
                    project_name=metadata["project_name"],
                    project_price=metadata["project_price"],
                    tax_amount=metadata["tax_amount"],
                    final_amount=metadata["final_amount"],
                    order_number=metadata["order_number"],
                    payment_type=payment_type.name,
                    payment_status=status_name,
                    payment_date=payment_record.created_at,
                    language=metadata["language"],
                )

                message = (
                    f"用户 - {metadata['user_name']}, \n{metadata['user_email']} 完成了一笔支付\n\n"
                    f"订单信息:\n"
                    f"订单号: {metadata['order_number']}\n"
                    f"原始金额: ${float(metadata['project_price']):.2f}\n"
                    f"税费: ${float(metadata['tax_amount']):.2f}\n"
                    f"最终金额: ${float(metadata['final_amount']):.2f}\n"
                    f"支付方式: {payment_type.name}\n"
                    f"日期: {payment_record.created_at}\n"
                    f"请登录后台管理页面查看详情。\n"
                )
                notification_task.delay(
                    notification_type=NotificationType.PAYMENT_REQUEST.value,
                    message=message,
                )
                self.logger.info(f"支付通知已发送，订单号: {metadata['order_number']}")
            except Exception as e:
                self.logger.error(
                    f"发送支付通知失败，订单号: {metadata['order_number']}, 错误: {str(e)}"
                )

    async def stripe_webhook(self, request: Request):
        """Stripe 支付回调处理"""
        try:
            event = stripe.Webhook.construct_event(
                await request.body(),
                request.headers.get("Stripe-Signature"),
                settings.stripe.STRIPE_WEBHOOK_SECRET.get_secret_value(),
            )
        except stripe.error.SignatureVerificationError:
            self.logger.error("Stripe webhook signature verification failed")
            raise HTTPException(status_code=400, detail="Invalid signature")
        except Exception as e:
            self.logger.error(f"Stripe webhook event parsing failed: {str(e)}")
            raise HTTPException(
                status_code=400, detail="Invalid webhook event")

        event_handlers = {
            "payment_intent.succeeded": lambda: self._process_payment_event(
                event["data"]["object"], PaymentStatus.success, "success"
            ),
            "payment_intent.payment_failed": lambda: self._process_payment_event(
                event["data"]["object"], PaymentStatus.failed, "failed"
            ),
            "payment_intent.canceled": lambda: self._process_payment_event(
                event["data"]["object"], PaymentStatus.cancel, "cancelled"
            ),
        }

        if event["type"] in event_handlers:
            return await event_handlers[event["type"]]()

        return {"status": "success"}

    async def get_payment_success_details(
        self, payment_intent_id: str
    ) -> Dict[str, Any]:
        """通过 payment_intent_id 获取支付成功的产品详情"""
        try:
            # 从 Stripe 获取支付意图详情
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            # 检查支付状态
            if payment_intent.status != "succeeded":
                raise HTTPException(
                    status_code=400,
                    detail=get_message(
                        "payment.common.paymentFailed"),
                )

            # 提取元数据
            metadata = self._extract_payment_metadata(payment_intent)

            # 验证元数据
            if not self._validate_metadata(metadata):
                raise HTTPException(
                    status_code=400,
                    detail=get_message(
                        "payment.paymentSuccess.invalidMetadata"
                    ),
                )

            # 获取支付类型
            payment_type = self._get_payment_type_from_method(
                payment_intent.get("payment_method")
            )

            # 构建响应数据
            response = {
                "payment_intent_id": payment_intent_id,
                "payment_status": payment_intent.status,
                "order_number": metadata["order_number"],
                "payment_date": payment_intent.created,
                "user": {
                    "user_id": int(metadata["user_id"]),
                    "user_name": metadata["user_name"],
                    "user_email": metadata["user_email"],
                },
                "project": {
                    "project_id": int(metadata["project_id"]),
                    "cover_url": metadata["cover_url"],
                    "project_name": metadata["project_name"],
                    "project_description": metadata["project_description"],
                    "project_price": float(metadata["project_price"]),
                    "project_section_name": metadata.get("project_section_name", ""),
                    "project_slug": metadata.get("project_slug", ""),
                },
                "tax": {
                    "tax_name": metadata["tax_name"],
                    "tax_rate": float(metadata["tax_rate"]),
                    "tax_amount": float(metadata["tax_amount"]),
                },
                "final_amount": float(metadata["final_amount"]),
                "payment_type": payment_type.name,
            }

            self.logger.info(f"成功获取支付详情，订单号: {metadata['order_number']}")
            return response

        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe API 错误: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=get_message(
                    "payment.paymentSuccess.stripeError"),
            )
        except Exception as e:
            self.logger.error(f"获取支付详情时发生错误: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=get_message(
                    "payment.paymentSuccess.internalError"),
            )

    async def get_payment_record(
        self,
        user_id: int,
        role: RoleType,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if role == RoleType.user:
            return await self.payment_crud.get_payment_record(
                
                page=page,
                size=size,
                user_id=user_id,
                role=role,
            )
        else:
            return await self.payment_crud.get_payment_record(
                
                page=page,
                size=size,
                role=role,
            )


def get_payment_service(
    payment_crud: PaymentCrud = Depends(get_payment_crud),
) -> PaymentService:
    """获取支付服务实例"""
    return PaymentService(payment_crud)
