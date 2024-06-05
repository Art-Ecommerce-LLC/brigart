function toggleIcon() {
    const icon = document.querySelector('#nav-icon3');
    icon.classList.toggle('open');

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
        displayCustomMessage(emailInput, 'Your email is not valid. Please try again', 'error-msg');
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
        displayCustomMessage(emailInput, 'Your email has been added to the email list', 'confirmation-msg');
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
// function submitForm(img_url, title, method) {
//     let requestOptions = {
//         headers: {
//             'Content-Type': 'application/json'
//         }
//     };
    
//     if (method === 'POST') {
//         requestOptions.method = 'POST';
//         requestOptions.body = JSON.stringify({ url: img_url , title1 : title});
//     }

//     fetch('/shop', requestOptions)
//     .then(response => response.json())
//     .then(data => {
//         console.log(data);
//         // Once the POST request is successful, you can redirect to the GET endpoint
//         window.location.href = '/shop';
//     })
//     .catch(error => {
//         console.error('Error:', error);
//     });
// }
function submitForm(title) {
    // Redirect to the GET endpoint with the title as a path parameter
    // replace the spaces with pluses
    title = title.replace(/ /g, '+');
    window.location.href = '/shop/' + title;
}

function toggleDropdown() {
    const dropdown = document.querySelector('.mobile-dropdown');
    const glance_h1 = document.querySelector('.glance_inner h1');
    const content = document.querySelector('.content');
    const footer = document.querySelector('.footer');
    // Toggle the 'show' class to control visibility
    dropdown.classList.toggle('show');
    content.classList.toggle('hide');
    footer.classList.toggle('hide'); // Add or remove 'hide' class to hide or show the content
    // Lock the page from scrolling when the dropdown is open
    if (dropdown.classList.contains('show')) {
        document.body.style.overflow = 'hidden';
        glance_h1.style.display = 'none'
    } else {
        document.body.style.overflow = 'auto';
        glance_h1.style.display = 'block'
        content.classList.remove('hide');
        footer.classList.remove('hide');
    }

}
function toggleMenu() {
    const navbar = document.querySelector('.navbar');
    const mobileMenu = document.querySelector('.mobile-menu');
    const dropdown = document.querySelector('.mobile-dropdown')
    const glance_h1 = document.querySelector('.glance_inner h1');
    const content = document.querySelector('.content');
    const footer = document.querySelector('.footer');
    // Toggle the 'show' class to control visibility

    // Toggle the mobile menu
    if (window.innerWidth <= 827) {
        navbar.style.display = 'none';
        mobileMenu.style.display = 'flex';
        document.body.style.overflow = 'auto';
        if (dropdown.classList.contains('show')) {
            document.body.style.overflow = 'hidden';
            glance_h1.style.display = 'none';
            content.classList.add('hide');
            footer.classList.add('hide');
            
        }
        else {
            document.body.style.overflow = 'auto';
            glance_h1.style.display = 'block';
            content.classList.remove('hide');
            footer.classList.remove('hide');
        }

    } else {
        navbar.style.display = 'flex';
        mobileMenu.style.display = 'none';
        document.body.style.overflow = 'auto';
        glance_h1.style.display = 'block'
        content.classList.remove('hide');
        footer.classList.remove('hide');
    }


}

// Initial toggle when the page loads
document.addEventListener('DOMContentLoaded', function() {
    updateCartQuantity();
    toggleMenu();

    // Check on scroll
    window.addEventListener('resize', toggleMenu);
    document.getElementById('currentYear').innerText = new Date().getFullYear();

});

// Toggle the menu on window resize



function loadImagesInView() {
    const artworks = document.querySelectorAll('.artwork');

    artworks.forEach((artwork, index) => {
        const rect = artwork.getBoundingClientRect();
        const windowHeight = window.innerHeight;

        if (rect.top < windowHeight && rect.bottom >= 0) {
            // Load the image source if it's within the viewport
            const imgSrc = artwork.getAttribute('style');
            if (imgSrc) {
                artwork.setAttribute('style', imgSrc);
            }
        }
    });
}

function checkFade() {
    const artworks = document.querySelectorAll('.artwork');

    artworks.forEach((artwork, index) => {
        const rect = artwork.getBoundingClientRect();
        const windowHeight = window.innerHeight;
        const leftDistance = rect.left; // Distance from the left edge of the viewport

        if (rect.top < windowHeight && rect.bottom >= 0) {
            // Calculate delay based on the distance from the left edge
            const delay = leftDistance * 0.4; // Adjust the multiplier for the desired delay

            // Add a timeout to apply the fade-in class with delay
            setTimeout(() => {
                artwork.classList.add('fade-in');
            }, delay);
        }
    });
}

// Load images when the page is loaded
document.addEventListener('DOMContentLoaded', function() {

    loadImagesInView();
    window.addEventListener('load', function() {
        checkFade();
    });

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




// Load images when scrolling
window.addEventListener('scroll', function() {
    loadImagesInView();
    checkFade();
});

// Load images when resizing the window
window.addEventListener('resize', function() {
    loadImagesInView();
    checkFade();
});
// Initial check on page load
