
function submitForm(title) {
    // Redirect to the GET endpoint with the title as a path parameter
    // replace the spaces with pluses
    title = title.replace(/ /g, '+');
    window.location.href = '/shop/' + title;
}

// Initial toggle when the page loads
document.addEventListener('DOMContentLoaded', function() {
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
