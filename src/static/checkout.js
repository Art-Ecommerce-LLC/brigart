document.addEventListener("DOMContentLoaded", () => {
  const stripe = Stripe("pk_test_51PUCroP7gcDRwQa36l19NuC5DMT7t5wJVn0HEY73nAKbRO7BmozSO2XTSMW6qLPIB7Y6hrJrag5jnnbMY6QgPvoz00la6BYXMS");


  e.preventDefault();
  setLoading(true); // Show spinner when the contact form is submitted

  initialize(); // Wait for Stripe elements to load before proceeding
  checkStatus();



  document
    .querySelector("#payment-form")
    .addEventListener("submit", handleSubmit);

  async function initialize() {
    
    const response = await fetch("/create-payment-intent", {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });
    const { clientSecret } = await response.json();

    const appearance = { theme: 'stripe' };
    elements = stripe.elements({ appearance, clientSecret });

    const paymentElementOptions = { 
      layout: "tabs", 
      mode: "payment" 
    };
    const paymentElement = elements.create("payment", paymentElementOptions);
    const paymentElementPromise = new Promise((resolve) => {
      paymentElement.mount("#payment-element");
      paymentElement.on('ready', resolve);
    });

    const addressElementOptions = {
      mode: 'shipping',
      fields: { phone: 'always' },
    };
    const addressElement = elements.create("address", addressElementOptions);
    const addressElementPromise = new Promise((resolve) => {
      addressElement.mount("#shipping-element");
      addressElement.on('ready', resolve);
    });

    // Wait for both elements to be ready before hiding the spinner
    await Promise.all([paymentElementPromise, addressElementPromise]);
    document.querySelector(".submit-payment").classList.add("show");
    setLoading(false); // Hide spinner when Stripe elements are ready
  }

  async function get_session_id() {
    try {
      const response = await fetch("/get_session_id", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      const data = await response.json();
      console.log("Session ID received:", data.session_id); // Log the received sessionId
      return data.session_id; // Ensure the correct key is used
    } catch (error) {
      console.error("Error fetching session id:", error);
      throw error; // Rethrow error to be caught in calling function
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);

    const sessionId = await get_session_id();
    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
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

    setTimeout(() => {
      messageContainer.classList.add("hidden");
      messageContainer.textContent = "";
      shippingMessageContainer.classList.add("hidden");
      shippingMessageContainer.textContent = "";
    }, 4000);
  }

  function setLoading(isLoading) {
    const inputs = document.querySelectorAll('input, textarea, select, button');
    inputs.forEach(input => input.readOnly = isLoading);

    const submitButton = document.querySelector("#submit");
    
    if (isLoading) {
      let spinner = document.querySelector('.spinner');
      if (!spinner) {
        spinner = document.createElement('div');
        spinner.classList.add('spinner');
        paynowButton.classList.add('hide');
        document.body.appendChild(spinner);
      }
      spinner.style.display = 'block';
      document.body.style.opacity = '0.5';

      // Preserve the size of the submit button
      submitButton.style.width = `${submitButton.offsetWidth}px`;
      submitButton.style.height = `${submitButton.offsetHeight}px`;
      submitButton.disabled = true;
    } else {
      const spinner = document.querySelector('.spinner');
      if (spinner) {
        spinner.style.display = 'none';
        document.body.style.opacity = '1';
      }

      submitButton.style.width = '';
      submitButton.style.height = '';
      submitButton.disabled = false;
    }
  }
});
