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

function updateCartQuantity(lockPage = false) {
    if (lockPage) {
        // Lock the user from clicking anything
        document.body.style.pointerEvents = 'none';

        // Dim the entire page
        const overlay = document.createElement('div');
        overlay.classList.add('overlay');
        document.body.appendChild(overlay);

        // Display the loading bar
        const loadingBar = document.createElement('div');
        loadingBar.classList.add('loading-bar');
        document.body.appendChild(loadingBar);
    }

    fetch('/get_cart_quantity') // Assuming you have an endpoint to get cart quantity
        .then(response => response.json())
        .then(data => {
            if (data.quantity !== 0) {
                document.getElementById('cartQuantity').innerText = data.quantity;
                document.getElementById('mobileCartQuantity').innerText = data.quantity;

                // Unlock the page after the cart quantity is updated
                document.body.style.pointerEvents = 'auto';

                // Remove the overlay and loading bar
                const overlay = document.querySelector('.overlay');
                const loadingBar = document.querySelector('.loading-bar');
                if (overlay) overlay.remove();
                if (loadingBar) loadingBar.remove();
            } else {
                document.getElementById('cartQuantity').innerText = '';
                document.getElementById('mobileCartQuantity').innerText = '';
                // Add a button right below h1 with id more shop that leads to /shop_art_menu 
                const moreShop = document.createElement('button');
                moreShop.innerText = 'Continue Shopping';
                moreShop.addEventListener('click', () => {
                    window.location.href = '/shop_art_menu';
                });
                moreShop.classList.add('more-shop-styles');
                // put inside the shop-more div
                document.querySelector('.shop-more').appendChild(moreShop);

                // Unlock the page even if cart quantity is 0
                document.body.style.pointerEvents = 'auto';

                // Remove the overlay and loading bar
                const overlay = document.querySelector('.overlay');
                const loadingBar = document.querySelector('.loading-bar');
                if (overlay) overlay.remove();
                if (loadingBar) loadingBar.remove();
            }
        })
        .catch(error => {
            console.error('Error:', error);

            // Unlock the page on error
            document.body.style.pointerEvents = 'auto';

            // Remove the overlay and loading bar
            const overlay = document.querySelector('.overlay');
            const loadingBar = document.querySelector('.loading-bar');
            if (overlay) overlay.remove();
            if (loadingBar) loadingBar.remove();
        });
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
function increaseQuantity(button) {
    getCartQuantity().then(cartQuantity => {
        console.log(cartQuantity);
        let quantityElement = button.parentElement.querySelector('.quantity-input');
        let quantityPrice = button.parentElement.parentElement.parentElement.querySelector('.price');
        
        let currentQuantity = parseInt(quantityElement.value);



        if (cartQuantity  >= 1000) {
            // Display a message above the total price
            displayTotalQuantityError('The maximum quantity allowed is 1000.');
            return; // Exit the function early to prevent further execution
        }

        // Calculate the new quantity
        let newQuantity = currentQuantity + 1;

        // Check if increasing the quantity will exceed 1000
        if (newQuantity > 1000) {
            // Display a message above the total price
            displayTotalQuantityError('The maximum quantity allowed is 1000.');
            return; // Exit the function early to prevent further execution
        }

        // Update the UI with the new quantity
        quantityElement.value = newQuantity;// Update the cart quantity
        // update the value of the input field instead of inner text
        
        quantityPrice.innerText = '$' + newQuantity * 225;

        // Make the API call only if the new quantity is within the limit
        let img_url = button.parentElement.parentElement.parentElement.querySelector('img').src;
        let img_title = button.parentElement.parentElement.parentElement.querySelector('.title_container p').innerText;

        let requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: img_url, title1: img_title })
        };

        fetch('/increase_quantity', requestOptions)
            .then(response => {

                if (!response.ok) {
                    return;
                } else {
                    updateTotalPrice();
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
        updateCartQuantity(true);
}

function decreaseQuantity(button) {
    let quantityElement = button.parentElement.querySelector('.quantity-input');
    let quantityPrice = button.parentElement.parentElement.querySelector('.price');

    let currentQuantity = parseInt(quantityElement.value);

    if (currentQuantity > 1) {
        quantityElement.value = currentQuantity - 1;
        quantityPrice.innerText = '$' + (currentQuantity - 1) * 225;
        let img_url = button.parentElement.parentElement.parentElement.querySelector('img').src;
        let img_title = button.parentElement.parentElement.parentElement.querySelector('.title_container p').innerText;

        let requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: img_url, title1: img_title})
        };

        fetch('/decrease_quantity', requestOptions)
        .then(response => {
            if (!response.ok) {
                console.error('Failed to decrease quantity');
            }
            else {
                updateTotalPrice();
                
                // Remove the error message if it exists
                removeMaxQuantityErrorMessage(); // Remove the error message here
            }
            
        })
        .catch(error => {
            console.error('Error:', error);
        });
        
        updateCartQuantity(true);

    } else {
        removeItem(button);
        // Remove the error message when quantity reaches 0
        updateCartQuantity(true);
        removeMaxQuantityErrorMessage(); // Remove the error message here as well
    }
}

function removeItem(button) {
    // Remove the line element

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
        body: JSON.stringify({ url: img_url, title1 : img_title})
    };

    fetch('/delete_item', requestOptions)
    .then(response => {
        if (!response.ok) {
            console.error('Failed to delete item');
        }
        else {
            updateTotalPrice();
            

            // Remove the error message if it exists
            removeMaxQuantityErrorMessage(); // Remove the error message here
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
    updateCartQuantity(true);
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
    updateCartQuantity(true);
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
// Toggle the menu on window resize
window.addEventListener('resize', toggleMenu);

