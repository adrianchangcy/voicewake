import stripe
from voicewake import settings
#possible to-do
#payment table might need idempotency_key column
#do some odd evaluation on 1/5 ratings that lead to talker bans
#do some odd evaluation on 1/5 ratings that lead to listener bans
#evaulate cases where refund is automatic out of good will

#plan
#fix everything to USD on website, then let Stripe do conversion
#use Stripe redirect, no custom payment flow (not needed and we have time constraint)



#PART 1
#when customer is performing checkout, create a session for it
def create_checkout_session():

    #when finalising, see here on how to customise the checkout page
    #https://stripe.com/docs/payments/checkout/customization

    stripe.api_key = settings.STRIPE_SECRET_KEY

    #create Product object
    stripe_product = stripe.Product.create(
        name='Coffee for the talker \nHehehe',
        images=['https://thumbs.dreamstime.com/b/smiling-clown-colorful-background-face-over-41547240.jpg'],
        metadata={
            'talker_event_id':'talker_event_id',
            'listener_event_id':'listener_event_id',
        }
    )

    #create Price object
    stripe_price = stripe.Price.create(
        unit_amount=500,
        currency='usd',
        product=stripe_product.id,
    )

    #create Customer object
    stripe_customer = stripe.Customer.create(
        name='username',
        metadata={
            'user_id':'user_id'
        }
    )

    #create checkout Session object to save checkout progress
    checkout_sesison = stripe.checkout.Session.create(
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
        line_items=[
            #one dict for one product
            {
                "price": stripe_price,
                "quantity": 1,
            },
        ],
        mode="payment",
        customer=stripe_customer,
    )

    print(checkout_sesison)
    # from django.http import JsonResponse
    # return JsonResponse({'id':checkout_sesison.id})

def when_done_put_stripe_in_this_try_block():

    #handle errors gracefully
    try:

        pass

    except stripe.error.CardError as e:

        # Since it's a decline, stripe.error.CardError will be caught

        print('Status is: %s' % e.http_status)
        print('Code is: %s' % e.code)
        # param is '' in this case
        print('Param is: %s' % e.param)
        print('Message is: %s' % e.user_message)

    except stripe.error.RateLimitError as e:

        # Too many requests made to the API too quickly
        pass

    except stripe.error.InvalidRequestError as e:

        # Invalid parameters were supplied to Stripe's API
        pass

    except stripe.error.AuthenticationError as e:

        # Authentication with Stripe's API failed
        # (maybe you changed API keys recently)
        pass

    except stripe.error.APIConnectionError as e:

        # Network communication with Stripe failed
        pass

    except stripe.error.StripeError as e:

        # Display a very generic error to the user, and maybe send
        # yourself an email
        pass

    except Exception as e:
        # Something else happened, completely unrelated to Stripe
        pass

create_checkout_session()


















