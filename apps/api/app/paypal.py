import paypalrestsdk
from typing import Dict, Optional
from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class PayPalProvider:
    """PayPal micropayments provider for small transactions."""
    
    def __init__(self):
        self.api = paypalrestsdk.Api({
            'mode': settings.paypal_environment,  # 'sandbox' or 'live'
            'client_id': settings.paypal_client_id,
            'client_secret': settings.paypal_client_secret
        })
        
    def create_payment(
        self,
        amount_cents: int,
        job_id: str,
        description: str,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None
    ) -> Dict:
        """Create PayPal payment for micropayments.
        
        Args:
            amount_cents: Payment amount in cents
            job_id: Translation job ID for tracking
            description: Payment description
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
            customer_email: Optional customer email
            
        Returns:
            dict: Payment response with approval_url and payment_id
        """
        try:
            # Convert cents to dollars for PayPal
            amount_dollars = f"{amount_cents / 100:.2f}"
            
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": success_url,
                    "cancel_url": cancel_url
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": description,
                            "sku": job_id,
                            "price": amount_dollars,
                            "currency": "USD",
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": amount_dollars,
                        "currency": "USD"
                    },
                    "description": description,
                    "custom": job_id,  # Store job_id for webhook processing
                    "soft_descriptor": "EPUB Translator"
                }]
            }, api=self.api)
            
            if payment.create():
                logger.info(f"PayPal payment created: {payment.id} for job {job_id}")
                
                # Find approval URL
                approval_url = None
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break
                
                return {
                    'success': True,
                    'payment_id': payment.id,
                    'approval_url': approval_url,
                    'status': payment.state
                }
            else:
                logger.error(f"PayPal payment creation failed: {payment.error}")
                return {
                    'success': False,
                    'error': payment.error
                }
                
        except Exception as e:
            logger.error(f"PayPal payment creation exception: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_payment(self, payment_id: str, payer_id: str) -> Dict:
        """Execute approved PayPal payment.
        
        Args:
            payment_id: PayPal payment ID
            payer_id: PayPal payer ID from approval
            
        Returns:
            dict: Execution result with status and transaction details
        """
        try:
            payment = paypalrestsdk.Payment.find(payment_id, api=self.api)
            
            if payment.execute({"payer_id": payer_id}):
                logger.info(f"PayPal payment executed: {payment_id}")
                
                # Extract transaction details
                transaction = payment.transactions[0]
                custom_data = transaction.custom  # This should contain job_id
                
                return {
                    'success': True,
                    'payment_id': payment_id,
                    'status': payment.state,
                    'job_id': custom_data,
                    'amount_paid': float(transaction.amount.total),
                    'transaction_id': transaction.related_resources[0].sale.id
                }
            else:
                logger.error(f"PayPal payment execution failed: {payment.error}")
                return {
                    'success': False,
                    'error': payment.error
                }
                
        except Exception as e:
            logger.error(f"PayPal payment execution exception: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_details(self, payment_id: str) -> Dict:
        """Get PayPal payment details.
        
        Args:
            payment_id: PayPal payment ID
            
        Returns:
            dict: Payment details
        """
        try:
            payment = paypalrestsdk.Payment.find(payment_id, api=self.api)
            
            transaction = payment.transactions[0]
            
            return {
                'success': True,
                'payment_id': payment_id,
                'status': payment.state,
                'job_id': transaction.custom,
                'amount': float(transaction.amount.total),
                'currency': transaction.amount.currency,
                'payer_email': payment.payer.payer_info.email if payment.payer.payer_info else None,
                'created_time': payment.create_time,
                'updated_time': payment.update_time
            }
            
        except Exception as e:
            logger.error(f"PayPal get payment details exception: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def get_paypal_provider() -> PayPalProvider:
    """Get configured PayPal provider instance."""
    return PayPalProvider()


def should_use_paypal_micropayments(amount_cents: int) -> bool:
    """Determine if PayPal micropayments should be used based on amount.
    
    Args:
        amount_cents: Payment amount in cents
        
    Returns:
        bool: True if should use PayPal micropayments, False for Stripe
    """
    # Use PayPal for amounts below threshold (default $8.00)
    # PayPal micropayments: 5% + $0.05 = better for small amounts
    # Stripe: 2.9% + $0.30 = better for larger amounts
    return amount_cents < settings.micropayments_threshold_cents