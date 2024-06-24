
const stripe = Stripe("pk_test_51PUCroP7gcDRwQa36l19NuC5DMT7t5wJVn0HEY73nAKbRO7BmozSO2XTSMW6qLPIB7Y6hrJrag5jnnbMY6QgPvoz00la6BYXMS");


document.addEventListener('DOMContentLoaded', function() {

    // Initialize sections
    initializeSections();

    document.querySelectorAll('.collapsible-header').forEach(header => {
        header.addEventListener('click', () => {
            const section = header.parentElement;
            if (!header.classList.contains('disabled') || section.classList.contains('open')) {
                section.classList.toggle('open');
                updateArrow(header);
            }
        });
    });

    const continueButton = document.querySelector('#shippingInfoSection .continue-btn');
    continueButton.addEventListener('click', maskCreditCardAndCVV);
});

function initializeSections() {
    const sections = document.querySelectorAll('.collapsible-section');
    sections.forEach(section => {
        if (!section.classList.contains('open')) {
            section.classList.add('collapsed');
        }
    });
}


// The items the customer wants to buy
async function getOrderContents() {
  let response = await fetch("/get_order_contents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    });
    return await response.json();
}

initialize();
checkStatus();

document
  .querySelector("#payment-form")
  .addEventListener("submit", handleSubmit);


// Fetches a payment intent and captures the client secret
async function initialize() {
    let items = await getOrderContents()
      .then((data) => {
          return data;
          })
      .catch((error) => {
          console.error("Error:", error);
      }
      );
    console.log(items);
    const response = await fetch("/create-payment-intent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({order_contents : items}),
    });
    const { clientSecret } = await response.json();
  
    const appearance = {
      theme: 'stripe',
    };
    const elements = stripe.elements({ appearance, clientSecret });
  
    const paymentElementOptions = {
      layout: "tabs",
    };
  
    const paymentElement = elements.create("payment", paymentElementOptions);
    paymentElement.mount("#payment-element");
  
    // Create an address element
    const addressElementOptions = {
      mode: 'shipping', // Ensure it's set to 'shipping'
    };
    const addressElement = elements.create("address", addressElementOptions);
    addressElement.mount("#shipping-element"); // Corrected the ID to match your HTML
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
      }
      );
  
    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        // Make sure to change this to your payment completion page
        return_url: `http://localhost:8000/confirmation/${sessionId}`,
      },
    });
  
    // This point will only be reached if there is an immediate error when
    // confirming the payment. Otherwise, your customer will be redirected to
    // your `return_url`. For some payment methods like iDEAL, your customer will
    // be redirected to an intermediate site first to authorize the payment, then
    // redirected to the `return_url`.
    if (error.type === "card_error" || error.type === "validation_error") {
      showMessage(error.message);
    } else {
      showMessage("An unexpected error occurred.");
    }
  
    setLoading(false);
  }
  
  
function showMessage(messageText) {
    const messageContainer = document.querySelector("#payment-message");
  
    messageContainer.classList.remove("hidden");
    messageContainer.textContent = messageText;
  
    setTimeout(function () {
      messageContainer.classList.add("hidden");
      messageContainer.textContent = "";
    }, 4000);
  }
// Fetches the payment intent status after payment submission
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
  
  
  // Show a spinner on payment submission
function setLoading(isLoading) {
    if (isLoading) {
      // Disable the button and show a spinner
      document.querySelector("#submit").disabled = true;
      document.querySelector("#spinner").classList.remove("hidden");
      document.querySelector("#button-text").classList.add("hidden");
    } else {
      document.querySelector("#submit").disabled = false;
      document.querySelector("#spinner").classList.add("hidden");
      document.querySelector("#button-text").classList.remove("hidden");
    }
  }

function maskCreditCardAndCVV() {
    // Mask the credit card number except for the last four digits
    const cardNumberInput = document.getElementById('card-number');
    const cardNumberValue = cardNumberInput.value.trim();
    if (cardNumberValue.length > 4) {
        const maskedCardNumber = '*'.repeat(cardNumberValue.length - 4) + cardNumberValue.slice(-4);
        cardNumberInput.value = maskedCardNumber;
    }

    // Mask the entire CVV
    const cvvInput = document.getElementById('cvv');
    const cvvValue = cvvInput.value.trim();
    if (cvvValue.length > 0) {
        cvvInput.value = '*'.repeat(cvvValue.length);
    }
}



function toggleIcon() {
    const icon = document.querySelector('#nav-icon3');
    icon.classList.toggle('open');
}

function toggleInputsAndButtons(section, disable) {

    const inputs = section.querySelectorAll('input');
    const buttons = section.querySelectorAll('button.continue-btn'); // Target 

    // Add the class disabled to the buttons and inputs to disable them
    inputs.forEach(input => {
        input.disabled = disable;
    });

    buttons.forEach(button => {
        button.disabled = disable;
    });
}
function toggleNextSection(currentSectionId, nextSectionId) {

    validateSection(currentSectionId).then(isValid => {
        if (isValid) {
            removeFormErrorMessage();
            if (currentSectionId === 'paymentInfoSection') {
                handlePurchase(currentSectionId);
                return;
            }
            const currentSection = document.getElementById(currentSectionId);
            const currentSectionHeader = currentSection.querySelector('.collapsible-header');
            currentSection.classList.remove('open');

            // Remove the continue button from the current section
            const continueButton = currentSection.querySelector('.continue-btn');
            if (continueButton) {
                continueButton.remove();
            }

            updateArrow(currentSectionHeader);
            toggleInputsAndButtons(currentSection, true);


            const nextSection = document.getElementById(nextSectionId);
            const nextSectionHeader = nextSection.querySelector('.collapsible-header');
            
            nextSection.classList.add('open');
            nextSectionHeader.classList.remove('disabled');
            nextSectionHeader.style.fontWeight = 'bold';
            updateArrow(nextSectionHeader);
            toggleInputsAndButtons(nextSection, false);
            // Scroll to the next section smoothly
        } else {
            // Display custom error message as the second to last element in the collapsible-content div in the current section
            displayErrorMessage(currentSectionId, 'Please enter a valid email and phone number.');
        }
    }).catch(error => {
        console.error('Validation failed:', error);
        displayErrorMessage(currentSectionId, 'An error occurred while validating. Please try again.');
    });
}
function removeFormErrorMessage() {
    const existingErrorMessage = document.querySelector('.error-message');
    if (existingErrorMessage) {
        existingErrorMessage.remove();
    }
}

function displayErrorMessage(currentSectionId, message) {
    // check if there is an existing error message
    const existingErrorMessage = document.querySelector('.error-message');
    if (existingErrorMessage) {
        existingErrorMessage.remove();
    }
    // Check if message is not null or empty
    if (message) {
        const currentSection = document.getElementById(currentSectionId);
        const content = currentSection.querySelector('.collapsible-content');
        const errorMessage = document.createElement('p');
        errorMessage.innerText = message;
        errorMessage.classList.add('error-message');
        content.insertBefore(errorMessage, content.lastElementChild);
    }

}

async function validateSection(sectionId) {
    const section = document.getElementById(sectionId);
    const inputs = section.querySelectorAll('input');

    if (sectionId === 'contactInfoSection') {
        const email = document.getElementById('email').value.trim();
        const phone = document.getElementById('phone').value.trim();
        if (!email || !phone) {
            return false;
        }

        // Send the email and phone in an async function that triggers the spinner and disables the buttons until the response is received
        const contact_payload = {
            email: email,
            phone: phone
        }
        const responsePromise = fetch('/validate_contact_info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(contact_payload)
        });

        // Use togglePageLock to manage the page lock and response handling
        return togglePageLock(responsePromise).then(response => {
            if (!response.ok) {
                return false;
            }
            removeFormErrorMessage();
            return true;
        });
    }
    if (sectionId === 'paymentInfoSection') {
        const cardName = document.getElementById('card-name').value.trim();
        const cardNumber = document.getElementById('card-number').value.trim();
        const expiryDate = document.getElementById('expiry').value.trim();
        const cvv = document.getElementById('cvv').value.trim();
        if (!cardName || !cardNumber || !expiryDate || !cvv) {
            return false;
        }

        // Send the card details in an async function that triggers the spinner and disables the buttons until the response is received
        const payment_payload = {
            cardName: cardName,
            cardNumber: cardNumber,
            expiryDate: expiryDate,
            cvv: cvv
        }

        const responsePromise = fetch('/validate_payment_info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payment_payload)
        });

        // Use togglePageLock to manage the page lock and response handling
        return togglePageLock(responsePromise).then(response => {
            if (!response.ok) {
                return false;
            }
            removeFormErrorMessage();
            return true;
        });
    }
    if (sectionId === 'billingAddressSection') {
        const fullname = document.getElementById('fullname').value.trim();
        const address1 = document.getElementById('address1').value.trim();
        const address2 = document.getElementById('address2').value.trim();
        const city = document.getElementById('city').value.trim();
        const state = document.getElementById('state').value.trim();
        const zip = document.getElementById('zip').value.trim();
        if (!fullname || !address1 || !city || !state || !zip) {
            return false;
        }

        billing_payload = {
            fullname: fullname,
            address1: address1,
            address2: address2,
            city: city,
            state: state,
            zip: zip
        }
        const responsePromise = fetch('/validate_shipping_info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(billing_payload)
        });

        // Use togglePageLock to manage the page lock and response handling
        return togglePageLock(responsePromise).then(response => {
            if (!response.ok) {
                return false;
            }
            removeFormErrorMessage();
            return true;
        });
    }

    return true;
}

function updateArrow(header) {
    const arrow = header.querySelector('.arrow');
    if (header.parentElement.classList.contains('open')) {
        arrow.style.transform = 'rotate(180deg)';
    } else {
        arrow.style.transform = 'rotate(0deg)';
    }
}

function setButtonsState(disabled) {
    const buttons = document.querySelectorAll('.increase-quantity, .decrease-quantity, .remove-item'); // Adjust the selector to match your button classes
    // Can you also disable any links on the page
    const links = document.querySelectorAll('a');
    links.forEach(link => link.disabled = disabled);
    buttons.forEach(button => button.disabled = disabled);
}

async function togglePageLock(responsePromise) {
    setButtonsState(true);
    document.body.style.opacity = '0.5';
    const spinner = document.createElement('div');
    spinner.classList.add('spinner');
    document.body.appendChild(spinner);

    try {
        let response = await responsePromise;
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        return response;
    } finally {
        // await sleep(2000)
        // Unlock the buttons and the page
        
        document.body.style.opacity = '1';
        spinner.remove();
    }
}
async function getCartQuantity() {
    return fetch('/get_cart_quantity')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            return data.quantity;
        })
        .catch(error => {
            console.error('Error fetching cart quantity:', error);
            return 0;
        });
}

async function getSessionId() {
    return fetch('/get_session_id')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            return data.session_id;
        })
        .catch(error => {
            console.error('Error fetching session ID:', error);
            return null;
        });
}

//Create a second toggle for the mobile menu to be a dropdown menu when hamburger icon is clicked
async function handlePurchase(sectionId) {
    // Grab the continue-btn in the sectionID
    const continueButton = document.getElementById(sectionId).querySelector('.continue-btn');
    // Disable the buttons and inputs in the section
    toggleInputsAndButtons(document.getElementById(sectionId), true);

    // Change the text of the continue button to "Purchase"
    continueButton.innerText = 'Purchase';

    // If it gets clicked while its text is "Purchase", then submit a fetch request

    // Get all disabled input text fields
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone');
    const cardNameInput = document.getElementById('card-name');
    const cardNumberInput = document.getElementById('card-number');
    const expiryInput = document.getElementById('expiry');
    const cvvInput = document.getElementById('cvv');
    const fullnameInput = document.getElementById('fullname');
    const address1Input = document.getElementById('address1');
    const address2Input = document.getElementById('address2');
    const cityInput = document.getElementById('city');
    const stateInput = document.getElementById('state');
    const zipInput = document.getElementById('zip');
    const sameAsShipping = document.getElementById('sameAsShipping');

    let checkout_payload = {
        email: emailInput.value,
        phone: phoneInput.value,
        cardName: cardNameInput.value,
        cardNumber: cardNumberInput.value,
        expiryDate: expiryInput.value,
        cvv: cvvInput.value,
        fullname: fullnameInput.value,
        address1: address1Input.value,
        address2: address2Input.value,
        city: cityInput.value,
        state: stateInput.value,
        zip: zipInput.value
    };

    if (!sameAsShipping.checked) {
        const shipFullname = document.getElementById('shipFullname');
        const shipAddress1 = document.getElementById('shipAddress1');
        const shipAddress2 = document.getElementById('shipAddress2');
        const shipCity = document.getElementById('shipCity');
        const shipState = document.getElementById('shipState');
        const shipZip = document.getElementById('shipZip');
        
        checkout_payload = {
            ...checkout_payload,
            shipFullname: shipFullname.value,
            shipAddress1: shipAddress1.value,
            shipAddress2: shipAddress2.value,
            shipCity: shipCity.value,
            shipState: shipState.value,
            shipZip: shipZip.value
        };
    }

    try {
        const response = await fetch('/purchase', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(checkout_payload)
        });

        if (response.ok) {
            // Redirect to the confirmation page

            const sessionid = await getSessionId();
            window.location.href = `/confirmation/${sessionid}`;
        } else {
            // Display an error message
            displayErrorMessage(sectionId, 'An error occurred while processing your purchase. Please try again.');
        }
    } catch (error) {
        console.error('Error:', error);
        displayErrorMessage(sectionId, 'An error occurred while processing your purchase. Please try again.');
    }
}

async function updateTotalPrice() {
    let totalPrice = 0;
    // Loop through each item in the cart
    document.querySelectorAll('.price').forEach(priceElement => {
        totalPrice += parseFloat(priceElement.innerText.replace('$', ''));
    });

    // Send the total price to the backend for verification
    try {
        console.log('Total price:', totalPrice)
        const response = await fetch('/post_total_price', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            
            body: JSON.stringify({ totalPrice: totalPrice })
        })
         .then(data => {
            return data.json();
        });
        const responseData = response;
        // Handle the response data
        if (responseData.totalPrice !== undefined && responseData.totalPrice !== null) {
                // Update the total price element
            console.log(responseData.totalPrice);
            document.getElementById('total-price').innerText = responseData.totalPrice.toFixed(2);
    
        } else {
            console.log('Total price is not valid');
        }
    } catch (error) {
        console.error('Error checking total price:', error);
    } 
}

let errorMessageElement; 
function removeErrorMessage() {
    // Check if there is an existing error message element
    if (errorMessageElement) {
        // Remove the existing error message element
        errorMessageElement.remove();
        errorMessageElement = null; // Reset the global variable
    }
}

function displayTotalQuantityError(message) {
    // Remove any existing error message
    removeErrorMessage();

    // Create a new error message element
    errorMessageElement = document.createElement('p');
    errorMessageElement.innerText = message;
    errorMessageElement.classList.add('error-message');

    // Get the parent element of the total price element
    const totalElement = document.querySelector('.total');

    // Insert the error message before the total price element
    totalElement.parentNode.insertBefore(errorMessageElement, totalElement);



}

async function modifyPaymentIntent(order_contents){
    const response = await fetch('/modify-payment-intent', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ order_contents: order_contents })
    });
    const data = await response.json();
    console.log(data);

}

async function increaseQuantity(button) {
    try {
        // Get the order contents



        setButtonsState(true);

        // Wait for the cart quantity to be fetched
        const cartQuantity = await getCartQuantity();

        // Get the necessary DOM elements
        let quantityElement = button.parentElement.querySelector('.quantity-input');
        let quantityPrice = button.parentElement.parentElement.parentElement.querySelector('.price');

        // Parse the current quantity
        let currentQuantity = parseInt(quantityElement.value);

        // Check if the current cart quantity is at or exceeds the maximum limit
        if (cartQuantity >= 1000) {
            displayTotalQuantityError('The maximum quantity allowed is 1000.');
            setButtonsState(false) // Re-enable the button
            return;
        }

        // Calculate the new quantity
        let newQuantity = currentQuantity + 1;

        // Check if increasing the quantity will exceed the maximum limit
        if (newQuantity > 1000) {
            displayTotalQuantityError('The maximum quantity allowed is 1000.');
            setButtonsState(false); // Re-enable the button
            return;
        }

        // Prepare the data for the API call
        let img_title = button.parentElement.parentElement.parentElement.querySelector('.title_container p').innerText;

        let requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({title: img_title})
        };

        let response = fetch('/increase_quantity', requestOptions);
        let responseData = await togglePageLock(response)
            .then((response) => {
                return response.json();
            });
        // Update the UI with the new quantity only after the API call succeeds
        quantityElement.value = newQuantity;
        quantityPrice.innerText = '$' + responseData.price;
        
        await updateCartQuantity(cartQuantity + 1);
        updateTotalPrice();
        removeMaxQuantityErrorMessage();
        
        let items = await getOrderContents()
            .then((data) => {
                return data;
                })
            .catch((error) => {
                console.error("Error:", error);
            }
            );

        modifyPaymentIntent(items);
        // Re-enable the button
        setButtonsState(false);
    } catch (error) {
        console.error('Error:', error);
        // Re-enable the button in case of error
        setButtonsState(false);
    }
}

async function decreaseQuantity(button) {
    try {
        // Disable the button to prevent rapid clicks
        setButtonsState(true);

        const cartQuantity = await getCartQuantity(); // Fetch the cart quantity
        let quantityElement = button.parentElement.querySelector('.quantity-input');
        let quantityPrice = button.parentElement.parentElement.querySelector('.price');

        let currentQuantity = parseInt(quantityElement.value);

        if (currentQuantity > 1) {
            let newQuantity = currentQuantity - 1;

            // Prepare the data for the API call
            let img_title = button.parentElement.parentElement.parentElement.querySelector('.title_container p').innerText;

            let requestOptions = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title: img_title})
            };

            let response = fetch('/decrease_quantity', requestOptions);
            let responseData = await togglePageLock(response)
                .then((response => {
                    return response.json();
                }));
            

            quantityElement.value = newQuantity;
            quantityPrice.innerText = '$' + responseData.price;
            await updateCartQuantity(cartQuantity - 1);
            updateTotalPrice();
            removeMaxQuantityErrorMessage();
            let items = await getOrderContents()
            .then((data) => {
                return data;
                })
            .catch((error) => {
                console.error("Error:", error);
            }
            );

            modifyPaymentIntent(items);
            setButtonsState(false);
        } else {
            await removeItem(button);
        }

        // Re-enable the button
        setButtonsState(false);
    } catch (error) {
        console.error('Error:', error);
        // Re-enable the button in case of error
        setButtonsState(false);
    }
}

async function removeItem(button) {
    try {
        // Find the closest quantity-container from the button
        const quantityContainer = button.closest('.quantity-container');
        
        // Select the quantity input and price text within this container
        const quantityElement = quantityContainer.querySelector('.quantity-input');
        const priceElement = quantityContainer.querySelector('.price');

        setButtonsState(true); // Disable the buttons to prevent rapid clicks

        const cartQuantity = await getCartQuantity(); // Fetch the cart quantity

        // Remove the item from the UI
        const infoContainer = button.closest('.info_container');
        infoContainer.remove();

        // Make the API call to delete the item
        let img_title = infoContainer.querySelector('.title_container p').innerText;
        
        let requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({title : img_title})
        };

        const response = fetch('/delete_item', requestOptions);
        const responseData = await togglePageLock(response);

        const input_quantity = parseInt(quantityElement.value);
        const updated_cart_quantity = cartQuantity - input_quantity;
        await updateCartQuantity(updated_cart_quantity); // Update cart quantity after removing the item
        updateTotalPrice(); // Update total price after updating cart quantity
        removeMaxQuantityErrorMessage(); // Remove the error message here
        let items = await getOrderContents()
            .then((data) => {
                return data;
                })
            .catch((error) => {
                console.error("Error:", error);
            }
            );

        modifyPaymentIntent(items);
        setButtonsState(false); // Re-enable the buttons
    } catch (error) {
        console.error('Error:', error);
        setButtonsState(false); // Re-enable the buttons in case of error
    }
}
async function removeItemButton(button) {
    try {
        // Find the closest quantity-container from the button
        const quantityContainer = button.closest('.quantity-container');
        
        // Select the quantity input and price text within this container
        const quantityElement = quantityContainer.querySelector('.quantity-input');
        const priceElement = quantityContainer.querySelector('.price');

        setButtonsState(true); // Disable the buttons to prevent rapid clicks

        const cartQuantity = await getCartQuantity(); // Fetch the cart quantity

        // Remove the item from the UI
        const infoContainer = button.closest('.info_container');
        infoContainer.remove();

        // Make the API call to delete the item
        let img_title = infoContainer.querySelector('.title_container p').innerText;
        
        let requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title : img_title})
        };

        const response = fetch('/delete_item', requestOptions);
        const responseData = await togglePageLock(response);

        const input_quantity = parseInt(quantityElement.value);
        const updated_cart_quantity = cartQuantity - input_quantity;
        await updateCartQuantity(updated_cart_quantity); // Update cart quantity after removing the item
        updateTotalPrice(); // Update total price after updating cart quantity
        removeMaxQuantityErrorMessage(); // Remove the error message here
        setButtonsState(false); // Re-enable the buttons
    } catch (error) {
        console.error('Error:', error);
        setButtonsState(false); // Re-enable the buttons in case of error
    }
}
function removeMaxQuantityErrorMessage() {
    // Check if there is an existing error message element for maximum quantity
    const errorMessage = document.querySelector('.error-message');
    if (errorMessage) {
        // Remove the error message
        errorMessage.remove();
    }
}

async function updateCartQuantity(cart_quantity) {
        if (cart_quantity !== 0) {
            document.getElementById('cartQuantity').innerText = cart_quantity;
            document.getElementById('mobileCartQuantity').innerText = cart_quantity;
        } else {
            document.getElementById('cartQuantity').innerText = '';
            document.getElementById('mobileCartQuantity').innerText = '';
            // Only create and add the "Continue Shopping" button once
            // add style to content to hide it
            document.querySelector('.left-section').classList.add('hide');
            document.querySelector('.right-section').classList.add('hide');
            document.querySelector('.content').classList.add('show');
            if (!document.querySelector('.shop-more button')) {
                const moreShop = document.createElement('button');
                // Add claslist element hid eto checkout-container
                document.querySelector('.checkout-container').classList.add('hide');
                moreShop.innerText = 'Continue Shopping';
                moreShop.addEventListener('click', () => {
                    window.location.href = '/shop_art_menu';
                });
                moreShop.classList.add('more-shop-styles');
                document.querySelector('.shop-more').appendChild(moreShop);
            }
        return Promise.resolve();
}}
function toggleDropdown() {
    const dropdown = document.querySelector('.mobile-dropdown');
    const content = document.querySelector('.content');
    const footer = document.querySelector('.footer');
    // Toggle the 'show' class to control visibility
    dropdown.classList.toggle('show');
    content.classList.toggle('hide');
    footer.classList.toggle('hide'); // Add or remove 'hide' class to hide or show the content

    // Lock the page from scrolling when the dropdown is open
    if (dropdown.classList.contains('show')) {
        document.body.style.overflow = 'hidden';
    } else {
        document.body.style.overflow = 'auto';
    }
}

function toggleMenu() {
    const navbar = document.querySelector('.navbar');
    const mobileMenu = document.querySelector('.mobile-menu');
    const content = document.querySelector('.content');
    const footer = document.querySelector('.footer');
    const dropdown = document.querySelector('.mobile-dropdown');
    // Toggle the mobile menu
    if (window.innerWidth <= 827) {
        navbar.style.display = 'none';
        mobileMenu.style.display = 'flex';
        document.body.style.overflow = 'auto';
        if (dropdown.classList.contains('show')) {
            content.classList.add('hide');
            footer.classList.add('hide');
        }
        
    } else {
        navbar.style.display = 'flex';
        mobileMenu.style.display = 'none';
        document.body.style.overflow = 'auto';
        content.classList.remove('hide');
        footer.classList.remove('hide');
    }
}

// Initial toggle when the page loads
document.addEventListener('DOMContentLoaded', function() {
    getCartQuantity().then(cartQuantity => {
        updateCartQuantity(cartQuantity);
        toggleMenu();
        document.getElementById('currentYear').innerText = new Date().getFullYear();
        updateTotalPrice();
});
});
// Toggle the menu on window resize
window.addEventListener('resize', toggleMenu);

