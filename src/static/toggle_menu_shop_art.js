function toggleIcon() {
    const icon = document.querySelector('#nav-icon3');
    icon.classList.toggle('open');

}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function increaseQuantity(button) {
    try {
        // Disable the button to prevent rapid clicks
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
            setButtonsState(false); // Re-enable the button
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

        let img_title = button.parentElement.parentElement.parentElement.querySelector('.title_container p').innerText;

        let requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title: img_title })
        };

        let response = fetch('/increase_quantity', requestOptions);
        let responseData = await togglePageLock(response);
        // Check if response data ok

        if (responseData) {
            // Update the UI with the new quantity only after the API call succeeds
            quantityElement.value = newQuantity;
            console.log(responseData);

            quantityPrice.innerText = '$' + responseData.price;
            await updateCartQuantity(cartQuantity + 1);
            updateTotalPrice();
            removeMaxQuantityErrorMessage();
        }

        // Re-enable the button
        setButtonsState(false);
    } catch (error) {
        console.error('Error:', error);
        // Re-enable the button in case of error
        setButtonsState(false);
    }
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
        
        return response.json();
    } finally {
        // Unlock the buttons and the page
        document.body.style.opacity = '1';
        spinner.remove();
    }
}

function setButtonsState(disabled) {
    const buttons = document.querySelectorAll('.increase-quantity, .decrease-quantity, .remove-item'); // Adjust the selector to match your button classes
    // Can you also disable any links on the page
    const links = document.querySelectorAll('a');
    links.forEach(link => link.disabled = disabled);
    buttons.forEach(button => button.disabled = disabled);
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


// Updates the UI on the page to reflect the cart quantity
async function updateCartQuantity(cart_quantity) {
    if (cart_quantity !== 0) {
        document.getElementById('cartQuantity').innerText = cart_quantity;
        document.getElementById('mobileCartQuantity').innerText = cart_quantity;
    } else {
        document.getElementById('cartQuantity').innerText = '';
        document.getElementById('mobileCartQuantity').innerText = '';
        // Add a button right below h1 with id moreShop that leads to /shop_art_menu 
        // Add the hide class to the checkout-container div
        document.querySelector('.checkout-container').classList.add('hide');


        const moreShop = document.createElement('button');
        moreShop.innerText = 'CONTINUE SHOPPING';
        moreShop.addEventListener('click', () => {
            window.location.href = '/shop_art_menu';
        });
        moreShop.classList.add('more-shop-styles');
        // put inside the shop-more div
        document.querySelector('.shop-more-wrapper').appendChild(moreShop);
    }
    return Promise.resolve(); // Ensure it returns a promise
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
    errorMessageElement.classList.add('error-msg');

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
            setButtonsState(false); // Re-enable the button
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


        let img_title = button.parentElement.parentElement.parentElement.querySelector('.title_container p').innerText;

        let requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({title: img_title })
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
        // Get the necessary DOM elements
        let quantityElement = button.parentElement.querySelector('.quantity-input');
        let quantityPrice = button.parentElement.parentElement.parentElement.querySelector('.price');

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
        const quantityElement = button.parentElement.querySelector('.quantity-input');

        setButtonsState(true); // Disable the buttons to prevent rapid clicks

        const cartQuantity = await getCartQuantity(); // Fetch the cart quantity

        // Remove the item from the UI
        button.parentElement.parentElement.parentElement.remove();

        // Make the API call to delete the item
        let img_title = button.parentElement.parentElement.parentElement.querySelector('.title_container p').innerText;
        
        let requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({title: img_title})
        };

        let response = fetch('/delete_item', requestOptions);
        let responseData = await togglePageLock(response)
            .then((response) => {
                return response.json();
            });
        
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
            body: JSON.stringify({ title: img_title })
        };

        let response = fetch('/delete_item', requestOptions);
        let responseData = await togglePageLock(response)
            .then((response) => {
                return response.json();
            });
        // update the total price

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