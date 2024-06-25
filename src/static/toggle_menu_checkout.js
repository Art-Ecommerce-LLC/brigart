
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

async function updateTotalPrice() {
    let totalPrice = 0;
    // Loop through each item in the cart
    document.querySelectorAll('.price').forEach(priceElement => {
        totalPrice += parseFloat(priceElement.innerText.replace('$', ''));
    });

    // Send the total price to the backend for verification
    try {
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

    // get email input value
    const response = await fetch('/modify-payment-intent', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ order_contents: order_contents})
    });
    const data = await response.json();
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
        dropdown.classList.remove('show');
        dropdown.classList.add('hide');
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

