document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('artworkContainer');
    let draggingElement;

    console.log("DOM fully loaded and parsed");

    container.addEventListener('dragstart', function (e) {
        draggingElement = e.target;
        e.dataTransfer.setData('text/plain', e.target.dataset.index);
        console.log("Drag started for element with index:", e.target.dataset.index);
    });

    container.addEventListener('dragover', function (e) {
        e.preventDefault();
        const target = e.target.closest('.artwork-item');
        if (target && target !== draggingElement) {
            container.insertBefore(draggingElement, target);
            console.log("Element moved. New order:");
            Array.from(container.children).forEach((item, index) => {
                console.log(`Index: ${index}, Title: ${item.querySelector('input[name="art_order[]"]').value}`);
            });
        }
    });

    container.addEventListener('drop', function (e) {
        e.preventDefault();
    });

    // Send the new order to the server using fetch
    document.getElementById('artworkForm').addEventListener('submit', function (e) {
        e.preventDefault(); // Prevent the default form submission

        const order = Array.from(container.children).map((item, index) => ({
            title: item.querySelector('input[name="art_order[]"]').value,
            sortOrder: index + 1
        }));

        console.log("Sending the following order:", order);

        fetch('/update_artwork_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(order)
        })
        .then(response => {
            console.log("Response status:", response.status);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log("Order updated successfully:", data);
            window.location.href = "/"; // Redirect after success
        })
        .catch(error => {
            console.error('Error in updating artwork order:', error);
        });
    });
});
