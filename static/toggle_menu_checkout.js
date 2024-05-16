
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
//Create a second toggle for the mobile menu to be a dropdown menu when hamburger icon is clicked
function handlePurchase(button) {
    // Gather form data
    const email = document.getElementById("email").value;
    const phone = document.getElementById("phone").value;
    const cardName = document.getElementById("card-name").value;
    const cardNumber = document.getElementById("card-number").value;
    const expiryDate = document.getElementById("expiry").value;
    const cvv = document.getElementById("cvv").value;
    const fullname = document.getElementById("fullname").value;
    const address1 = document.getElementById("address1").value;
    const address2 = document.getElementById("address2").value;
    const city = document.getElementById("city").value;
    const state = document.getElementById("state").value;
    const zip = document.getElementById("zip").value;

    // Now you have all the form data stored in variables
    // You can use this data to process the purchase, send it to the server, etc.
    // For example, you can make a fetch request to a backend endpoint to process the payment

    const formData = {
        email : email,
        phone : phone,
        cardName : cardName,
        cardNumber : cardNumber,
        expiryDate : expiryDate,
        cvv : cvv,
        fullname : fullname,
        address1 : address1,
        address2 : address2,
        city : city,
        state : state,
        zip : zip,
    };

    // Make a fetch request to send the form data to the backend
    fetch('/process_payment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Handle the response data
        console.log(data);
        // Redirect to a success page, display a success message, etc.
        window.location.href = '/';

    })
    .catch(error => {
        console.error('Error processing payment:', error);
        // Handle the error, display an error message, etc.
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
            await updateCartQuantity(0); // Await updateCartQuantity
            updateTotalPrice(); // Update total price after updating cart quantity
            removeMaxQuantityErrorMessage(); // Remove the error message here
        }
    } catch (error) {
        console.error('Error:', error);
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

async function updateCartQuantity() {
    try {
        const response = await fetch('/get_cart_quantity');
        const data = await response.json();
        if (data.quantity !== 0) {
            document.getElementById('cartQuantity').innerText = data.quantity;
            document.getElementById('mobileCartQuantity').innerText = data.quantity;
        } else {
            document.getElementById('cartQuantity').innerText = '';
            document.getElementById('mobileCartQuantity').innerText = '';
            // Only create and add the "Continue Shopping" button once
            if (!document.querySelector('.shop-more button')) {
                const moreShop = document.createElement('button');
                moreShop.innerText = 'Continue Shopping';
                moreShop.addEventListener('click', () => {
                    window.location.href = '/shop_art_menu';
                });
                moreShop.classList.add('more-shop-styles');
                document.querySelector('.shop-more').appendChild(moreShop);
            }
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function toggleDropdown() {
    const dropdown = document.querySelector('.mobile-dropdown');
    const content = document.querySelector('.content');
    const footer = document.querySelector('.footer');
    const body = document.querySelector('body');
    // Toggle the 'show' class to control visibility
    dropdown.classList.toggle('show');
    content.classList.toggle('hide');
    footer.classList.toggle('hide'); // Add or remove 'hide' class to hide or show the content

    // Lock the page from scrolling when the dropdown is open
    if (dropdown.classList.contains('show')) {
        document.body.style.overflow = 'hidden';
        body.style.overflowY = 'hidden';
    } else {
        document.body.style.overflow = 'auto';
        body.style.overflowY = 'auto';
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

