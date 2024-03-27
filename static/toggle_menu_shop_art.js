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
            else {
                document.getElementById('cartQuantity').innerText = '';
                document.getElementById('mobileCartQuantity').innerText = '';
                // Add a button right below h1 with id more shopp that leads to /shop_art_menu 
                const moreShop = document.createElement('button');
                moreShop.innerText = 'Continue Shopping';
                moreShop.addEventListener('click', () => {
                    window.location.href = '/shop_art_menu';
                });
                moreShop.classList.add('more-shop-styles');
                // put inside the shop-more div
                document.querySelector('.shop-more').appendChild(moreShop);
                    
            }
        })
        .catch(error => {
            console.error('Error:', error);
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


function increaseQuantity(button) {
    let quantityElement = button.parentElement.parentElement.querySelector('p');
    let quantityPrice = button.parentElement.parentElement.querySelector('.price');
    let currentQuantity = parseInt(quantityElement.innerText);

    quantityElement.innerText = currentQuantity + 1;
    quantityPrice.innerText = '$' + (currentQuantity + 1) * 225;

    let img_url = button.parentElement.parentElement.parentElement.querySelector('img').src;
    let img_title = button.parentElement.parentElement.parentElement.querySelector('.title_container h2').innerText;

    let requestOptions = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: img_url, title1 : img_title})
    };

    fetch('/increase_quantity', requestOptions)
    .then(response => {
        if (!response.ok) {
            console.error('Failed to increase quantity');
        }
        else {
            updateTotalPrice();
            updateCartQuantity();
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function decreaseQuantity(button) {
    let quantityElement = button.parentElement.parentElement.querySelector('p');
    let currentQuantity = parseInt(quantityElement.innerText);
    let quantityPrice = button.parentElement.parentElement.querySelector('.price');


    if (currentQuantity > 1) {
        quantityElement.innerText = currentQuantity - 1;
        quantityPrice.innerText = '$' + (currentQuantity - 1) * 225;
        let img_url = button.parentElement.parentElement.parentElement.querySelector('img').src;
        let img_title = button.parentElement.parentElement.parentElement.querySelector('.title_container h2').innerText;

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
                updateCartQuantity();
            }
            
        })
        .catch(error => {
            console.error('Error:', error);
        });
    
    

    } else {
        removeItem(button);
    }
}

function removeItem(button) {
    // Remove the line element
    let lineElement = button.parentElement.parentElement.parentElement.nextElementSibling;
    if (lineElement && lineElement.classList.contains('line')) {
        lineElement.remove();
    }

    // Remove the item from the UI
    button.parentElement.parentElement.parentElement.remove();

    // Make the API call to delete the item
    let img_url = button.parentElement.parentElement.parentElement.querySelector('img').src;
    let quantity = button.parentElement.parentElement.querySelector('p').innerText;
    let img_title = button.parentElement.parentElement.parentElement.querySelector('.title_container h2').innerText;
    
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
            updateCartQuantity();
        }
    })
    .catch(error => {
        console.error('Error:', error);
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
    if (window.innerWidth <= 768) {
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
    updateTotalPrice();

    // Add event listener to the checkout button
    document.querySelector('.checkout-btn').addEventListener('click', function() {
        // Redirect to the /checkout endpoint
        let totalPrice = parseFloat(document.getElementById('total-price').innerText.replace('$', ''));
        if (totalPrice === 0) {
            alert('Your cart is empty');
            return;
        } else {
            window.location.href = '/checkout';
        }
    });

});
// Toggle the menu on window resize
window.addEventListener('resize', toggleMenu);

