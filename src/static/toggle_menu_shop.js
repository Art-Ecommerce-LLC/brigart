function toggleIcon() {
    const icon = document.querySelector('#nav-icon3');
    icon.classList.toggle('open');

}
async function togglePageLockShop(title) {
    // Change the opacity of the body to 0.5 before starting the addToCart function
    document.body.style.opacity = '0.5';
    
    // Add a spinner to indicate loading
    const spinner = document.createElement('div');
    spinner.classList.add('spinner');
    document.body.appendChild(spinner);

    quantityInputValue = document.getElementById('quantity-input').value;

    try {
        // Await the addToCart function
        await addToCart(title, quantityInputValue);
    } finally {
        // Change the opacity back to 1 once the addToCart function is done
        document.body.style.opacity = '1';
        // Remove the spinner once the addToCart function is done
        spinner.remove();
    }
}

async function getCartQuantity() {
    try {
        const response = await fetch('/get_cart_quantity');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        return data.quantity; 
    } catch (error) {
        console.error('Error fetching cart quantity:', error);
        return 0;
    }
}


async function updateCartQuantity(cart_quantity) {
    if (cart_quantity !== 0) {
        document.getElementById('cartQuantity').innerText = cart_quantity;
        document.getElementById('mobileCartQuantity').innerText = cart_quantity;
    } else {
        document.getElementById('cartQuantity').innerText = '';
        document.getElementById('mobileCartQuantity').innerText = '';
    }
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


async function addToCart(title, quantityInputValue) {
    if (isNaN(quantityInputValue)) {
        displayQuantityErrorMessage();
        return;
    }

    if (quantityInputValue > 1000 || quantityInputValue < 1) {
        displayQuantityErrorMessage();
        return;
    }

    // Grab current quantity from the cartQuantity element
    const currentQuantity = parseInt(document.getElementById('cartQuantity').innerText, 10);
    if (currentQuantity + parseInt(quantityInputValue) > 1000) {
        displayTotalQuantityErrorMessage();
        return;
    }

    try {
        const cart_quantity = await submitPostForm(quantityInputValue, title);

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

        const addToCartButton = document.getElementById('addToCartLink');
        addToCartButton.textContent = 'Checkout';
        addToCartButton.classList.remove('add-to-cart-btn');
        addToCartButton.classList.add('checkout-btn');
        addToCartButton.setAttribute('onclick', 'checkoutRedirect(); return false;');
        await updateCartQuantity(cart_quantity);
    } catch (error) {
        displayTotalQuantityErrorMessage();
        console.error('Error:', error);
    }

    document.getElementById('quantity-input').value = '1';
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

async function submitPostForm(quantity, title) {

    const requestData = {
        quantity: parseInt(quantity, 10), // Ensure quantity is an integer
        title: title
    };
    try {
        const response = await fetch('/shop_art', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const quantityData = await response.json();
        const cart_quantity = quantityData.quantity;
        return cart_quantity;
    } catch (error) {
        console.error('Error:', error);
        // Display an error message to the user if needed
        displayTotalQuantityErrorMessage();
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
document.addEventListener('DOMContentLoaded', async function() {
    toggleMenu();
    document.getElementById('currentYear').innerText = new Date().getFullYear();
    // Attach event listeners to the increment and decrement buttons
    document.getElementById('increment-btn').addEventListener('click', incrementQuantity);
    document.getElementById('decrement-btn').addEventListener('click', decrementQuantity);
     // Call addToCart with quantityInputValue set to 0 to get the total cart quantity
    try {
        const cartQuantity = await getCartQuantity();
        await updateCartQuantity(cartQuantity);
    } catch (error) {
        console.error('Error fetching cart quantity on page load:', error);
    }
    const titleDiv = document.getElementById('title');
    const titleH2 = titleDiv.querySelector('h2');
    if (titleH2.textContent === 'None') {
        window.location.href = '/';
    }
    
});

// Toggle the menu on window resize
window.addEventListener('resize', toggleMenu);