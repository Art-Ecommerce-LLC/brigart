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
function handlePurchase() {
    // Gather form data
    const cardName = document.getElementById("card_name").value;
    const cardNumber = document.getElementById("card_number").value;
    const expiryDate = document.getElementById("expiry_date").value;
    const cvv = document.getElementById("cvv").value;

    // Send data to the backend
    fetch('/process_payment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            card_name: cardName,
            card_number: cardNumber,
            expiry_date: expiryDate,
            cvv: cvv
        })
    })
    .then(response => {
        if (response.ok) {
            // Parse JSON response only once
            return response.json();
        }
        throw new Error('Network response was not ok.');
    })
    .then(data => {
        // Handle success response
        alert(data.message); // Assuming the response contains a message field
        // Redirect to the home page after alert is closed
        window.location.href = "/";
    })
    .catch(error => {
        // Handle error
        alert('There was an error processing your payment. Please try again later.');
        console.error('There was a problem with the fetch operation:', error);
    });
}
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
        mobileMenu.style.display = 'block';
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
});
// Toggle the menu on window resize
window.addEventListener('resize', toggleMenu);

