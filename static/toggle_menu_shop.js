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

let messageAdded = false; // Flag to track if the message has been added

function addToCart(img_url, title) {
    if (!messageAdded) {
        let quantityInputValue = document.getElementById('quantity-input').value;
        
        const quantityBox = document.getElementById('quantityBox');
        quantityBox.style.display = 'none';
        
        // Change the text of the button to "Checkout" and change its class
        const addToCartButton = document.getElementById('addToCartLink');
        addToCartButton.textContent = 'Checkout';
        addToCartButton.classList.remove('add-to-cart-btn'); // Remove the old class
        addToCartButton.classList.add('checkout-btn'); // Add the new class
        addToCartButton.setAttribute('onclick', 'checkoutRedirect(); return false;'); // Add onclick event for checkout

        submitPostForm(img_url, quantityInputValue, title)
            .then(data => {
                // Create a new div for the message container
                
                const messageDiv = document.createElement('div');
                messageDiv.classList.add('message-container'); // Add a class for styling

                // Create the message element
                const messageContainer = document.createElement('p');
                messageContainer.textContent = 'Item added to cart!';
                messageContainer.classList.add('confirmation-msg'); // Add the specified CSS class

                // Append the message to the message container div
                messageDiv.appendChild(messageContainer);

                // Insert the message container after the button container
                const buttonContainer = document.querySelector('.button-container');
                buttonContainer.parentNode.insertBefore(messageDiv, buttonContainer.nextSibling);

                // Update the cart quantity display
                updateCartQuantity();

                // Set the flag to true to indicate that the message has been added
                messageAdded = true;
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }

    // Reset the quantity back to 1
    document.getElementById('quantity-input').value = '1';
}

// Function to handle the checkout redirection
function checkoutRedirect() {
    window.location.href = '/shop_art';
}
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
                console.log(data);
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
    }
}

function toggleMenu() {
    const navbar = document.querySelector('.navbar');
    const mobileMenu = document.querySelector('.mobile-menu');
    const content = document.querySelector('.content');
    const footer = document.querySelector('.footer');
    const dropdown = document.querySelector('.mobile-dropdown');
    // Toggle the mobile menu
    if (window.innerWidth <= 811) {
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
});

// Toggle the menu on window resize
window.addEventListener('resize', toggleMenu);

