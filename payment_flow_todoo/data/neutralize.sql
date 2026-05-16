-- disable paypal payment provider
UPDATE payment_provider
   SET flow_api_key = NULL,
       flow_private_key = NULL;
