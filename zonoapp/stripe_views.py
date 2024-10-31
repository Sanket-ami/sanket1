from django.shortcuts import render, redirect  # new
from django.conf import settings  # new
from django.urls import reverse  # new
from .models import Credits, PaymentStatus
import stripe  # new


def home(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    if request.method == "POST":
        user_price = float(request.POST.get("price")) * 100  # Convert to cents for Stripe
        product = stripe.Product.create(name="Custom Amount")
        price = stripe.Price.create(
            unit_amount=int(user_price), 
            currency="usd",
            product=product.id,
        )

        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": price.id,
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=request.build_absolute_uri(reverse("success")),
            cancel_url=request.build_absolute_uri(reverse("cancel")),
        )
        request.session['amount_paid'] = user_price / 100  
        request.session['payment_response'] = price.id

        return redirect(checkout_session.url, code=303)

    return render(request, "pages/payment/home.html")

def success(request):
    amount_paid = request.session.get('amount_paid')
    request.session.pop('amount_paid', None)    
    try:
        credits_remaining = Credits.objects.get(organisation_name=request.user.organisation_name)
    except Credits.DoesNotExist:
        credits_remaining = Credits.objects.create(
                organisation_name=request.user.organisation_name,
        )
    PaymentStatus.objects.create(
        organisation_name=request.user.organisation_name,
        user_id=request.user.id,
        status="success",
        amount=amount_paid,
        payment_response=request.session.get('payment_response')
    )
    credits_remaining.balance += int(amount_paid)
    credits_remaining.save()
    return render(request, "pages/payment/success.html", {"amount_paid": amount_paid})


def cancel(request):
    return render(request, "pages/payment/cancel.html")