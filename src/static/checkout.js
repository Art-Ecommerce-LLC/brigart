document.addEventListener("DOMContentLoaded", () => {
  const stripe = Stripe("pk_test_51PUCroP7gcDRwQa36l19NuC5DMT7t5wJVn0HEY73nAKbRO7BmozSO2XTSMW6qLPIB7Y6hrJrag5jnnbMY6QgPvoz00la6BYXMS");

  document.querySelector('#contact-form').addEventListener("submit", (e) => {
    e.preventDefault();
    const emailInput = document.getElementById('email');
    console.log(emailInput.value);

    initialize(emailInput.value);
    checkStatus();

    document
      .querySelector("#payment-form")
      .addEventListener("submit", handleSubmit);
  });

  async function getOrderContents(emailInput) {
    let response = await fetch("/get_order_contents", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: emailInput }),
    });
    return await response.json();
  }

  let elements;

  async function initialize(emailInput) {
    let items = await getOrderContents(emailInput)
      .then((data) => {
        return data;
      })
      .catch((error) => {
        console.error("Error:", error);
      });
    
    const response = await fetch("/create-payment-intent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_contents: items}),
    });
    const { clientSecret } = await response.json();

    const appearance = {
      theme: 'stripe',
    };
    elements = stripe.elements({ appearance, clientSecret });

    const paymentElementOptions = {
      layout: "tabs",
    };

    const paymentElement = elements.create("payment", paymentElementOptions);
    paymentElement.mount("#payment-element");

    const addressElementOptions = {
      mode: 'shipping', // Ensure it's set to 'shipping'
      fields: {
        phone: 'always',
      },
    };
    const addressElement = elements.create("address", addressElementOptions);
    addressElement.mount("#shipping-element");
    addressElement.on('change', (event) => {
      if (event.complete) {
        const address = event.value.address;
        const phone = event.value.phone;
        console.log(address);
        console.log(phone);
      }
    });
  }

  async function getSessionId() {
    const response = await fetch("/get_session_id", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    return await response.json();
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);

    const sessionId = await getSessionId()
      .then((data) => {
        return data.session_id;
      })
      .catch((error) => {
        console.error("Error:", error);
      });

    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        // Make sure to change this to your payment completion page
        return_url: `http://localhost:8000/confirmation/${sessionId}`,
      },
    });

    if (error.type === "card_error" || error.type === "validation_error") {
      showMessage(error.message);
    } else {
      showMessage("An unexpected error occurred.");
    }

    setLoading(false);
  }

  async function checkStatus() {
    const clientSecret = new URLSearchParams(window.location.search).get(
      "payment_intent_client_secret"
    );

    if (!clientSecret) {
      return;
    }

    const { paymentIntent } = await stripe.retrievePaymentIntent(clientSecret);

    switch (paymentIntent.status) {
      case "succeeded":
        showMessage("Payment succeeded!");
        break;
      case "processing":
        showMessage("Your payment is processing.");
        break;
      case "requires_payment_method":
        showMessage("Your payment was not successful, please try again.");
        break;
      default:
        showMessage("Something went wrong.");
        break;
    }
  }

  function showMessage(messageText) {
    const messageContainer = document.querySelector("#payment-message");
    const shippingMessageContainer = document.querySelector("#shipping-message");

    shippingMessageContainer.classList.remove("hidden");
    shippingMessageContainer.textContent = messageText;
    messageContainer.classList.remove("hidden");
    messageContainer.textContent = messageText;

    setTimeout(function () {
      messageContainer.classList.add("hidden");
      messageContainer.textContent = "";
      shippingMessageContainer.classList.add("hidden");
      shippingMessageContainer.textContent = "";
    }, 4000);
  }

  function setLoading(isLoading) {
    if (isLoading) {
      document.querySelector("#submit").disabled = true;
      document.querySelector("#spinner").classList.remove("hidden");
      document.querySelector("#button-text").classList.add("hidden");
    } else {
      document.querySelector("#submit").disabled = false;
      document.querySelector("#spinner").classList.add("hidden");
      document.querySelector("#button-text").classList.remove("hidden");
    }
  }
});
