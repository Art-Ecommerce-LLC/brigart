async function togglePageLock(img_url, title) {
    // Change the opacity of the body to 0.5 before starting the addToCart function
    document.body.style.opacity = '0.5';
    
    // Add a spinner to indicate loading
    const spinner = document.createElement('div');
    spinner.classList.add('spinner');
    document.body.appendChild(spinner);

    try {
        // Await the addToCart function
        await addToCart(img_url, title);
    } finally {
        // Change the opacity back to 1 once the addToCart function is done
        document.body.style.opacity = '1';
        // Remove the spinner once the addToCart function is done
        spinner.remove();
    }
}

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

function updateCartQuantity() {
    fetch('/get_cart_quantity') // Assuming you have an endpoint to get cart quantity
        .then(response => response.json())
        
        .then(data => {
            if (data.quantity !== 0) {
                document.getElementById('cartQuantity').innerText = data.quantity;
                document.getElementById('mobileCartQuantity').innerText = data.quantity;
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}
let quantity = 1; // Initial quantity

function incrementQuantity() {
    quantity++;
    document.getElementById('quantity-input').value = quantity;
    
}

function decrementQuantity() {
    if (quantity > 1) {
        quantity--;
        document.getElementById('quantity-input').value = quantity;
        document.getElementById('price-text').innerText = '$' + (quantity * 225);
    }
}

let messageAdded = false;
// Flag to track if the message has been added


async function addToCart(img_url, title) {

    let quantityInputValue = document.getElementById('quantity-input').value;


    // turn the input value into an integer
    if (isNaN(quantityInputValue)) {
        displayQuantityErrorMessage();
        return;
    }

    if (quantityInputValue > 1000 || quantityInputValue < 1 ) {
        displayQuantityErrorMessage();
        return;
    }
    // Fetch the current cart quantity
    fetch('/get_cart_quantity')
        .then(response => response.json())
        .then(data => {
            // Check if adding the selected quantity will exceed the limit
            if (data.quantity + parseInt(quantityInputValue) > 1000) {
                displayTotalQuantityErrorMessage();
                return;
            }
            

            // Proceed with adding to cart if the limit is not exceeded
            if (!messageAdded) {
                submitPostForm(img_url, quantityInputValue, title)
                    .then(data => {
                        updateCartQuantity();
                        // delete the message-container div from the page
                        const messageDiv = document.querySelector('.message-container1');
                        const messageDiv2 = document.querySelector('.message-container2');
                        if (messageDiv) {
                            messageDiv.remove();
                            
                        }
                        if (messageDiv2) {
                            messageDiv2.remove();
                        }

                        const quantityBox = document.getElementById('quantityBox');
                        quantityBox.style.display = 'none';

                        // Change the text of the button to "Checkout" and change its class
                        const addToCartButton = document.getElementById('addToCartLink');
                        addToCartButton.textContent = 'Checkout';
                        addToCartButton.classList.remove('add-to-cart-btn'); // Remove the old class
                        addToCartButton.classList.add('checkout-btn'); // Add the new class
                        addToCartButton.setAttribute('onclick', 'checkoutRedirect(); return false;'); // Add onclick event for checkout
                    })
                    .catch(error => {

                        displayTotalQuantityErrorMessage();
                        console.error('Error:', error);
                    });
            }
            // Reset the quantity back to 1
            document.getElementById('quantity-input').value = '1';
        })
        .catch(error => {
            console.error('Error fetching cart quantity:', error);
        });
}
let errorMessageElement = null; // Global variable to store the error message element

function displayQuantityErrorMessage() {
    // Remove any existing error message
    removeErrorMessage();

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message-container1'); // Add a class for styling

    // Create the message element
    const messageContainer = document.createElement('p');
    messageContainer.textContent = 'Please enter a valid integer between 1 and 1000';
    messageContainer.classList.add('error-msg'); // Add the specified CSS class

    // Make the message appear between the quantity box div with id quantityBox and form id myForm
    const quantityBox = document.getElementById('quantityBox');
    const form = document.getElementById('myForm');
    quantityBox.parentNode.insertBefore(messageDiv, form);

    // Append the message to the message container div
    messageDiv.appendChild(messageContainer);

    // Set the flag to true to indicate that the message has been added
    messageAdded1 = true;

    // Store the error message element in the global variable
    errorMessageElement = messageDiv;
}

function displayTotalQuantityErrorMessage(img_url, title) {
    // Remove any existing error message
    removeErrorMessage();

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message-container2'); // Add a class for styling

    // Create the message element
    const messageContainer = document.createElement('p');
    messageContainer.textContent = 'Your total quantity cannot exceed 1000';
    messageContainer.classList.add('error-msg'); // Add the specified CSS class

    // Make the message appear between the quantity box div with id quantityBox and form id myForm
    const quantityBox = document.getElementById('quantityBox');
    const form = document.getElementById('myForm');
    quantityBox.parentNode.insertBefore(messageDiv, form);

    // Append the message to the message container div
    messageDiv.appendChild(messageContainer);

    // Set the flag to true to indicate that the message has been added
    messageAdded2 = true;

    // Store the error message element in the global variable
    errorMessageElement = messageDiv;
}
function removeErrorMessage() {
    // Check if there is an existing error message element
    if (errorMessageElement) {
        // Remove the existing error message element
        errorMessageElement.remove();
        errorMessageElement = null; // Reset the global variable
    }
}
// Function to handle the checkout redirection
function checkoutRedirect() {
    window.location.href = '/shop_art';
}
// Disply a total qunatity error message if the submit post form returns an error

function submitPostForm(img_url, quantityInputValue, title) {
    return new Promise((resolve, reject) => {
        let requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: img_url, quantity: quantityInputValue, title2 : title })
        };

        fetch('/shop_art', requestOptions)
            .then(response => response.json())
            .then(data => {
                resolve(data); // Resolve the promise with the response data
            })
            .catch(error => {

                reject(error); // Reject the promise with the error
            });
    });
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
        content.classList.remove('hide');
        footer.classList.remove('hide');
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
    updateCartQuantity();
    toggleMenu();
    document.getElementById('currentYear').innerText = new Date().getFullYear();
    // Attach event listeners to the increment and decrement buttons
    document.getElementById('increment-btn').addEventListener('click', incrementQuantity);
    document.getElementById('decrement-btn').addEventListener('click', decrementQuantity);
    
    const titleDiv = document.getElementById('title');
    const titleH2 = titleDiv.querySelector('h2');
    if (titleH2.textContent === 'None') {
        window.location.href = '/';
    }
});

// Toggle the menu on window resize
window.addEventListener('resize', toggleMenu);

