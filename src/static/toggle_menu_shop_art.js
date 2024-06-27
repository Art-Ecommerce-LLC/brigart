function toggleIcon() {
    const icon = document.querySelector('#nav-icon3');
    icon.classList.toggle('open');

}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function togglePageLock(responsePromise) {
    document.body.style.opacity = '0.5';

    const spinner = document.createElement('div');
    spinner.classList.add('spinner');
    document.body.appendChild(spinner);

    try {
        const response = await responsePromise;
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        return response;
    } catch (error) {
        console.error('Error during fetch:', error);
        throw error;
    } finally {
        // Ensure spinner removal and page unlocking happen after response handling
        document.body.style.opacity = '1';
        spinner.remove();
        setButtonsState(false)// Re-enable the buttons here to ensure they are re-enabled even after an error
    }
}

function setButtonsState(boolean) {
    const links = document.querySelectorAll('a');
    const buttons = document.querySelectorAll('button');
    links.forEach(link => {
        link.disabled = boolean;
    });
    buttons.forEach(button => {
        button.disabled = boolean;
    });
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
    document.querySelectorAll('.price-container .price').forEach(priceElement => {
        let priceText = priceElement.innerText.replace('$', '').trim();
        let price = parseFloat(priceText);
        if (!isNaN(price)) {
            totalPrice += price;
        }
        console.log('Total price:', totalPrice);
        console.log('Price element:', priceElement.innerText);
    });

    try {
        const response = await fetch('/post_total_price', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ totalPrice: totalPrice })
        });

        const responseData = await response.json();
        if (responseData.totalPrice !== undefined && responseData.totalPrice !== null) {
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
        setButtonsState(true);

        const cartQuantity = await getCartQuantity();

        // Select related elements using parentElement and querySelector
        // let quantityElement = button.parentElement.parentElement.querySelector('.quantity-input-wrapper input');
        // let infoContainer = button.closest('.info_container');
        // let quantityPrice = infoContainer.querySelector('.price');
        // let img_title = infoContainer.querySelector('.title_container p').innerText;
        let quantityElement = button.parentElement.parentElement.querySelector(".quantity-input-wrapper input")
        // Parse the current quantity
        let quantityPrice = button.parentElement.parentElement.parentElement.querySelector('.price');
        let currentQuantity = parseInt(quantityElement.value);
        
        if (cartQuantity >= 1000) {
            displayTotalQuantityError('The maximum quantity allowed is 1000.');
            setButtonsState(false);
            return;
        }

        let newQuantity = currentQuantity + 1;

        if (newQuantity > 1000) {
            displayTotalQuantityError('The maximum quantity allowed is 1000.');
            setButtonsState(false);
            return;
        }
        let img_title = button.parentElement.parentElement.parentElement.parentElement.parentElement.querySelector('.title_container p').innerText;
        
        let requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title: img_title })
        };

        let response = fetch('/increase_quantity', requestOptions);
        let responseData = await togglePageLock(response)
            .then((response) => {
                return response.json();
            });
        
        
        // Update the UI
        quantityElement.value = newQuantity;
        quantityPrice.innerText = '$' + responseData.price;
        console.log('Quantity:', newQuantity);
        console.log('Price:', responseData.price);
        await updateCartQuantity(cartQuantity + 1);
        updateTotalPrice();
        removeMaxQuantityErrorMessage();
        setButtonsState(false);
        // Grab and Remove spinner element
        let spinner = document.querySelector('.spinner');
        spinner.remove();

    } catch (error) {
        console.error('Error:', error);
        setButtonsState(false);
    }
}


async function decreaseQuantity() {
    try {
        // Disable the button to prevent rapid clicks
        setButtonsState(true);

        const cartQuantity = await getCartQuantity(); // Fetch the cart quantity
        // Get the necessary DOM elements
        let quantityElement = document.querySelector('.quantity-input');
        let quantityPrice = document.querySelector('.price');
        let img_title = document.querySelector('.title_container p').innerText;

        let currentQuantity = parseInt(quantityElement.value);

        if (currentQuantity > 1) {
            let newQuantity = currentQuantity - 1;

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
            await updateTotalPrice();
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
        await updateTotalPrice(); // Update total price after updating cart quantity
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

async function get_session_id() {
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
            console.error('Error fetching session id:', error);
            return '';
        });
}

// Initial toggle when the page loads
document.addEventListener('DOMContentLoaded', async function() {
    getCartQuantity().then(cartQuantity => {
        updateCartQuantity(cartQuantity);
        toggleMenu();
        document.getElementById('currentYear').innerText = new Date().getFullYear();
        updateTotalPrice();
        let isMessageDisplayed = false;
        // Add event listener to the checkout button
        document.querySelector('.checkout-btn').addEventListener('click', async function() {
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
                await get_session_id().then(session_id => {
                    window.location.href = `/checkout/${session_id}`;
                });
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