function toggleIcon() {
    const icon = document.querySelector('#nav-icon3');
    icon.classList.toggle('open');
}
// Function to handle the checkout redirection
async function checkoutRedirect() {
    try {
        const sessionId = await get_session_id();
        console.log(sessionId); // Log the sessionId to check its value
        window.location.href = `/shop_art/${sessionId}`;
    } catch (error) {
        console.error('Error in checkoutRedirect:', error);
    }
}

async function paymentRedirect() {
    const session_id = await get_session_id();
    window.location.href = `/checkout/${session_id}`;
}
// Disply a total qunatity error message if the submit post form returns an error

async function get_session_id() {
    try {
        const response = await fetch('/get_session_id', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        console.log('Session ID received:', data.session_id); // Log the received sessionId
        return data.session_id; // Ensure the correct key is used
    } catch (error) {
        console.error('Error fetching session id:', error);
        throw error; // Rethrow error to be caught in calling function
    }
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
        const navbar = document.querySelector('.contact_form');;
        navbar.appendChild(customMessageElement);
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
function updateCartQuantityGeneral() {
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

function toggleDropdown() {
    const dropdown = document.querySelector('.mobile-dropdown');
    const glance_h1 = document.querySelector('.glance_inner h1');
    const glance = document.querySelector('.glance_inner');
    const content = document.querySelector('.content');
    const footer = document.querySelector('.footer');
    const pageLocationWrapper = document.querySelector('.page_location_wrapper');
    const collageWrapper = document.querySelector('.collage_wrapper');
    // Toggle the 'show' class to control visibility
    dropdown.classList.toggle('show');
    content.classList.toggle('hide');
    footer.classList.toggle('hide');
    if (collageWrapper) {
        collageWrapper.classList.toggle('hide');
    }
    if (pageLocationWrapper) {
        pageLocationWrapper.classList.toggle('hide');
    }
    if (glance_h1 && glance) {
        glance_h1.classList.toggle('hide-border');
        glance.classList.toggle('hide-border');
    } // Add or remove 'hide' class to hide or show the content
    // Lock the page from scrolling when the dropdown is open
    if (dropdown.classList.contains('show')) {
        document.body.style.overflow = 'hidden';
        if (collageWrapper) {
            collageWrapper.classList.add('hide');
        }
        if (glance_h1 && glance) {
            glance_h1.style.display = 'none'
            glance.classList.add('hide-border');
        }
        if (pageLocationWrapper) {
            pageLocationWrapper.classList.add('hide');
        }
    } else {
        document.body.style.overflow = 'auto';
        if (glance_h1 && glance) {
            glance_h1.style.display = 'block'
            glance.classList.remove('hide-border');
        }
        if (collageWrapper) {
            collageWrapper.classList.remove('hide');
        }
        if (pageLocationWrapper) {
            pageLocationWrapper.classList.remove('hide');
        }
        content.classList.remove('hide');
        footer.classList.remove('hide');
    }
}
function toggleMenu() {
    const navbar = document.querySelector('.navbar');
    const mobileMenu = document.querySelector('.mobile-menu');
    const dropdown = document.querySelector('.mobile-dropdown')
    const glance_h1 = document.querySelector('.glance_inner h1');
    const glance = document.querySelector('.glance_inner');
    const content = document.querySelector('.content');
    const footer = document.querySelector('.footer');
    const pageLocationWrapper = document.querySelector('.page_location_wrapper');
    const collageWrapper = document.querySelector('.collage_wrapper');
    // Toggle the 'show' class to control visibility

    // Toggle the mobile menu
    if (window.innerWidth <= 846) {
        navbar.style.display = 'none';
        mobileMenu.style.display = 'flex';
        document.body.style.overflow = 'auto';

        if (dropdown.classList.contains('show')) {
            document.body.style.overflow = 'hidden';
            if (glance_h1 && glance) {
                glance_h1.style.display = 'none';
                glance_h1.classList.add('hide-border');
                glance.classList.add('hide-border');
            }
            if (pageLocationWrapper) {
                pageLocationWrapper.classList.add('hide');
            }
            if (collageWrapper) {
                collageWrapper.classList.add('hide');
            }
            content.classList.add('hide');
            footer.classList.add('hide');
        
            
        }
        else {
            document.body.style.overflow = 'auto';
            if (glance_h1 && glance) {
                glance_h1.style.display = 'block';
                glance_h1.classList.remove('hide-border');
            }
            if (pageLocationWrapper) {
                pageLocationWrapper.classList.remove('hide');
            }
            if (collageWrapper) {
                collageWrapper.classList.remove('hide');
            }
            content.classList.remove('hide');
            footer.classList.remove('hide');

        }

    } else {
        navbar.style.display = 'flex';
        mobileMenu.style.display = 'none';
        document.body.style.overflow = 'auto';
        if (glance_h1){
            glance_h1.style.display = 'block';
            glance_h1.classList.remove('hide-border');
        }
        if (pageLocationWrapper) {
            pageLocationWrapper.classList.remove('hide');
        }
        if (collageWrapper) {
            collageWrapper.classList.remove('hide');
        }
        content.classList.remove('hide');
        footer.classList.remove('hide');
    }


}

// Initial toggle when the page loads
document.addEventListener('DOMContentLoaded', function() {
    updateCartQuantityGeneral();
    toggleMenu();

    // Check on scroll
    window.addEventListener('resize', toggleMenu);
    document.getElementById('currentYear').innerText = new Date().getFullYear();

});

// Toggle the menu on window resize

// Load images when the page is loaded
document.addEventListener('DOMContentLoaded', function() {

    const artworkImages = document.querySelectorAll('img.artwork[style]');

    artworkImages.forEach(img => {
        const tempVar = img.getAttribute('style');
        const preloadedImg = new Image();
        preloadedImg.src = tempVar;

        preloadedImg.onload = function() {
            img.src = preloadedImg.src;
        };
    });


});


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
async function togglePageLock(responsePromise) {
    setButtonsState(true); // Disable buttons
    document.body.style.opacity = '0.5'; // Dim the background

    // Create spinner wrapper
    const spinnerWrapper = document.createElement('div');
    spinnerWrapper.classList.add('spinner_wrapper');

    // Create spinner container
    const spinnerContainer = document.createElement('div');
    spinnerContainer.classList.add('spinner_container');

    // Create spinner
    const spinner = document.createElement('div');
    spinner.classList.add('spinner');

    // Append spinner to container, and container to wrapper
    spinnerContainer.appendChild(spinner);
    spinnerWrapper.appendChild(spinnerContainer);

    // Append wrapper to body
    document.body.appendChild(spinnerWrapper);

    try {
        const response = await responsePromise;
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response;
    } finally {
        document.body.style.opacity = '1'; // Restore background opacity
        spinnerWrapper.remove(); // Remove spinner from DOM
        setButtonsState(false); // Re-enable buttons
    }
}

function setButtonsState(disabled) {
    const buttons = document.querySelectorAll('.increase-quantity, .decrease-quantity, .remove-item');
    const links = document.querySelectorAll('a');
    links.forEach(link => link.style.pointerEvents = disabled ? 'none' : 'auto'); // Disable/enable links
    buttons.forEach(button => button.disabled = disabled);
}
