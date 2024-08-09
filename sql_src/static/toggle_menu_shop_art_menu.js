

function submitForm(title) {
    // Redirect to the GET endpoint with the title as a path parameter
    // replace the spaces with pluses
    title = title.replace(/ /g, '+');
    window.location.href = '/shop/' + title;
}


function checkFade() {
    const artworks = document.querySelectorAll('.artwork');
    const priceTags = document.querySelectorAll('.artwork-price');
    const titles = document.querySelectorAll('.artwork-name');

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
                titles[index].classList.add('fade-in');
                priceTags[index].classList.add('fade-in');
            }, delay);
        }
    });
}


// Load images when the page is loaded
document.addEventListener('DOMContentLoaded', function() {
    checkFade();
});

// Load images when scrolling
window.addEventListener('scroll', function() {
    checkFade();
});

// Load images when resizing the window
window.addEventListener('resize', function() {
    checkFade();
});