from django.conf import settings
from .models import Donation

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


def DonateCheckout(request):

    new_donation = Donation(
        tool_name="Climate Data Wrangler",
    )

    if request.method == "POST":
        token = request.POST.get("stripeToken")
        amount = request.POST.get("data-amount")
        currency = request.POST.get("data-currency")
        tool_name = request.POST.get("tool-name")
        user_email = request.POST.get("data-email")

        try:
            # amount must be in smallest units of currency (i.e. cents)
            amount = int(amount) * 100

            charge = stripe.Charge.create(
                api_key=stripe.api_key,
                amount=amount,
                currency=currency,
                source=token,
                description=tool_name,
                receipt_email=user_email,
            )

            new_donation.charge_id = charge.id
            new_donation.amount = amount / 100
            new_donation.currency = currency
            new_donation.tool_name = tool_name
            new_donation.email = user_email

        except stripe.error.CardError as ce:
            return HttpResponse(ce)

        else:
            new_donation.save()
            return HttpResponseRedirect(
                reverse('dkht:payment-success',
                        kwargs={'pk': new_donation.charge_id})
            )
            # The payment was successfully processed, the user's card was charged.
            # You can now redirect the user to another page or whatever you want
