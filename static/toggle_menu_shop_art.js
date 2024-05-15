// Returns cart quantity from python backend which takes the cookies and returns the total quantity
function getCartQuantity() {
    return fetch('/get_cart_quantity') // Assuming this endpoint returns the total quantity
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            return data.quantity; // Assuming the response has a 'quantity' property
        })
        .catch(error => {
            console.error('Error fetching cart quantity:', error);
            return 0; // Default to 0 in case of error
        });
}

function emailListEnter() {
    // Get the email input value
    const emailInput = document.getElementById('emailInput');
    const email = emailInput.value;

    // Check if an existing error message exists and remove it
    const existingErrorMessage = document.querySelector('.error-msg');
    if (existingErrorMessage) {
        existingErrorMessage.remove();
    }

    // Check if an existing confirmation message exists and remove it
    const existingConfirmationMsg = document.querySelector('.confirmation-msg');
    if (existingConfirmationMsg) {
        existingConfirmationMsg.remove();
    }

    // Validate the email format (you can add more robust validation)
    if (!isValidEmail(email)) {
        emailInput.value = '';
        // Display an error message next to the input box
        displayCustomMessage(emailInput, 'Your email is not valid. Please try again.', 'error-msg');
        return;
    }

    // Prepare the data to send to the backend
    const data = { email: email };

    // Send the data to your Python backend using fetch
    fetch('/subscribe', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        // Clear the input box after successful submission
        emailInput.value = '';
        // Display a confirmation message next to the input box
        displayCustomMessage(emailInput, 'Your email has been added to the email list.', 'confirmation-msg');
        return response.json();
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Function to display a custom message next to an input element
function displayCustomMessage(element, message, className) {
    // Check if a message element of the specified class already exists
    let customMessageElement = element.nextElementSibling;
    if (!customMessageElement || !customMessageElement.classList.contains(className)) {
        // If message element doesn't exist, create and append it
        const customMessageElement = document.createElement('p');
        customMessageElement.textContent = message;
        customMessageElement.classList.add(className); // Add the specified CSS class

        // Get the navbar div
        const navbar = document.querySelector('.footer_navbar');

        // Insert the message element into the navbar div
        navbar.insertBefore(customMessageElement, navbar.firstChild);

    // Scroll to the new message element
        customMessageElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
        // If message element already exists, update its content
        customMessageElement.textContent = message;
    }
}

// Basic email validation function
function isValidEmail(email) {
    // Basic email format validation using regex
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Updates the UI on the page to reflect the cart quantity
async function updateCartQuantity(cart_quantity) {
    if (cart_quantity !== 0) {
        document.getElementById('cartQuantity').innerText = cart_quantity;
        document.getElementById('mobileCartQuantity').innerText = cart_quantity;
    } else {
        document.getElementById('cartQuantity').innerText = '';
        document.getElementById('mobileCartQuantity').innerText = '';
        // Add a button right below h1 with id moreShop that leads to /shop_art_menu 
        const moreShop = document.createElement('button');
        moreShop.innerText = 'Continue Shopping';
        moreShop.addEventListener('click', () => {
            window.location.href = '/shop_art_menu';
        });
        moreShop.classList.add('more-shop-styles');
        // put inside the shop-more div
        document.querySelector('.shop-more').appendChild(moreShop);
    }
    return Promise.resolve(); // Ensure it returns a promise
}

function updateTotalPrice() {
    let totalPrice = 0;
    // Loop through each item in the cart
    document.querySelectorAll('.price').forEach(priceElement => {
        totalPrice += parseFloat(priceElement.innerText.replace('$', ''));
    });
    // Update the total price element
    document.getElementById('total-price').innerText = totalPrice.toFixed(2);
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
function removeMaxQuantityErrorMessage() {
    // Check if there is an existing error message element for maximum quantity
    const errorMessage = document.querySelector('.error-message');
    if (errorMessage) {
        // Remove the error message
        errorMessage.remove();
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

    // Scroll to the new message element
    errorMessageElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
async function increaseQuantity(button) {
    try {
        // Disable the button to prevent rapid clicks
        button.disabled = true;

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
            button.disabled = false; // Re-enable the button
            return;
        }

        // Calculate the new quantity
        let newQuantity = currentQuantity + 1;

        // Check if increasing the quantity will exceed the maximum limit
        if (newQuantity > 1000) {
            displayTotalQuantityError('The maximum quantity allowed is 1000.');
            button.disabled = false; // Re-enable the button
            return;
        }

        // Prepare the data for the API call
        let img_url = button.parentElement.parentElement.parentElement.querySelector('img').src;
        let img_title = button.parentElement.parentElement.parentElement.querySelector('.title_container p').innerText;

        let requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: img_url, title1: img_title })
        };

        const response = await fetch('/increase_quantity', requestOptions);

        if (response.ok) {
            // Update the UI with the new quantity only after the API call succeeds
            quantityElement.value = newQuantity;
            quantityPrice.innerText = '$' + newQuantity * 225;
            await updateCartQuantity(cartQuantity + 1);
            updateTotalPrice();
            removeMaxQuantityErrorMessage();
        }

        // Re-enable the button
        button.disabled = false;
    } catch (error) {
        console.error('Error:', error);
        // Re-enable the button in case of error
        button.disabled = false;
    }
}

async function decreaseQuantity(button) {
    try {
        // Disable the button to prevent rapid clicks
        button.disabled = true;

        const cartQuantity = await getCartQuantity(); // Fetch the cart quantity
        let quantityElement = button.parentElement.querySelector('.quantity-input');
        let quantityPrice = button.parentElement.parentElement.querySelector('.price');

        let currentQuantity = parseInt(quantityElement.value);

        if (currentQuantity > 1) {
            let newQuantity = currentQuantity - 1;

            // Prepare the data for the API call
            let img_url = button.parentElement.parentElement.parentElement.querySelector('img').src;
            let img_title = button.parentElement.parentElement.parentElement.querySelector('.title_container p').innerText;

            let requestOptions = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: img_url, title1: img_title })
            };

            const response = await fetch('/decrease_quantity', requestOptions);

            if (response.ok) {
                // Update the UI with the new quantity only after the API call succeeds
                quantityElement.value = newQuantity;
                quantityPrice.innerText = '$' + newQuantity * 225;
                await updateCartQuantity(cartQuantity - 1);
                updateTotalPrice();
                removeMaxQuantityErrorMessage();
            }
        } else {
            await removeItem(button);
        }

        // Re-enable the button
        button.disabled = false;
    } catch (error) {
        console.error('Error:', error);
        // Re-enable the button in case of error
        button.disabled = false;
    }
}


async function removeItem(button) {
    try {
        const cartQuantity = await getCartQuantity(); // Fetch the cart quantity

        // Remove the item from the UI
        button.parentElement.parentElement.parentElement.remove();

        // Make the API call to delete the item
        let img_url = button.parentElement.parentElement.parentElement.querySelector('img').src;
        let img_title = button.parentElement.parentElement.parentElement.querySelector('.title_container p').innerText;
        
        let requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: img_url, title1: img_title })
        };

        const response = await fetch('/delete_item', requestOptions);

        if (response.ok) {
            await updateCartQuantity(cartQuantity - 1); // Update cart quantity after removing the item
            updateTotalPrice(); // Update total price after updating cart quantity
            removeMaxQuantityErrorMessage(); // Remove the error message here

            // Check if the cart quantity is 0 and the "Continue Shopping" button doesn't already exist
            const moreShopButton = document.querySelector('.more-shop-styles');
            if (cartQuantity - 1 === 0 && !moreShopButton) {
                // Create and append the "Continue Shopping" button only if it doesn't exist
                const moreShopButton = document.createElement('button');
                moreShopButton.innerText = 'Continue Shopping';
                moreShopButton.addEventListener('click', () => {
                    window.location.href = '/shop_art_menu';
                });
                moreShopButton.classList.add('more-shop-styles');
                // put inside the shop-more div
                document.querySelector('.shop-more').appendChild(moreShopButton);
            } else if (cartQuantity - 1 > 0 && moreShopButton) {
                // If cart quantity is greater than 0 and the button exists, remove it
                moreShopButton.remove();
            }
        }
    } catch (error) {
        console.error('Error:', error);
    }
}



//Create a second toggle for the mobile menu to be a dropdown menu when hamburger icon is clicked
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
        let isMessageDisplayed = false;
        // Add event listener to the checkout button
        document.querySelector('.checkout-btn').addEventListener('click', function() {
            // Redirect to the /checkout endpoint
            let totalPrice = parseFloat(document.getElementById('total-price').innerText.replace('$', ''));
            if (totalPrice === 0 && !isMessageDisplayed) {
                // Instead of an alert, display a message above checkout-btn class saying Add Items To Cart to Checkout in the checkout-container class div only once if the button is clicked
                const checkoutContainer = document.querySelector('.checkout-container');
                const checkoutBtn = document.querySelector('.checkout-btn');
                const checkoutMessage = document.createElement('p');
                checkoutMessage.innerText = 'Add Items to Checkout';
                checkoutMessage.classList.add('empty-cart-message');
                checkoutContainer.insertBefore(checkoutMessage, checkoutBtn);

                isMessageDisplayed = true; // Set the flag to true after displaying the message

                return;
            } else if (totalPrice === 0 && isMessageDisplayed) {
                return; // Don't do anything if the message is already displayed
            } else {
                window.location.href = '/checkout';
            }
        });
        // Add event listener to the image click event
        const cartImage = document.querySelector('.cart-image');
        cartImage.addEventListener('click', function() {
            const checkoutContainer = document.querySelector('.checkout-container');
            const checkoutMessage = document.querySelector('.empty-cart-message');
            if (checkoutMessage) {
                checkoutContainer.removeChild(checkoutMessage);
                isMessageDisplayed = false; // Reset the flag when the message is removed
            }
        });
    });
});
// Toggle the menu on window resize
window.addEventListener('resize', toggleMenu);

