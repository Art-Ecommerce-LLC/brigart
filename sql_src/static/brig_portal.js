let openFormId = null;

function toggleForm(formId) {
    const form = document.getElementById(formId);
    const isOpen = form.style.display === 'block';

    // Close currently open form
    if (openFormId && openFormId !== formId) {
        document.getElementById(openFormId).style.display = 'none';
    }

    // Toggle the clicked form
    form.style.display = isOpen ? 'none' : 'block';
    openFormId = isOpen ? null : formId;
}



async function submitForm() {
    const form = document.getElementById('portal-form');
    const title = document.getElementById('title').value;
    const newTitle = document.getElementById('new-title').value;
    const fileInput = document.getElementById('file-upload');
    const messageDiv = document.getElementById('message');

    if (!title || !newTitle || !fileInput.files.length) {
        messageDiv.textContent = 'Please fill all the fields and upload a file.';
        messageDiv.style.display = 'block';
        messageDiv.style.color = 'red';
        return;
    }

    const formData = new FormData();
    formData.append('title', title);
    formData.append('new_title', newTitle);
    formData.append('file', fileInput.files[0]);

    try {
        const response = await fetch('/swap_image', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            messageDiv.textContent = result.message;
            messageDiv.style.display = 'block';
            messageDiv.style.color = 'green';
        } else {
            messageDiv.textContent = 'Submission failed. Please try again.';
            messageDiv.style.display = 'block';
            messageDiv.style.color = 'red';
        }
    } catch (error) {
        messageDiv.textContent = 'An error occurred. Please try again.';
        messageDiv.style.display = 'block';
        messageDiv.style.color = 'red';
    }
}
async function submitAddForm() {
    const form = document.getElementById('add-image-form');
    const titleInputs = document.querySelectorAll('input[name^="title_"]');
    const priceInputs = document.querySelectorAll('input[name^="price_"]');
    const fileInputs = document.getElementById('add-file-upload').files;
    const messageDiv = document.getElementById('message');

    if (titleInputs.length !== fileInputs.length || priceInputs.length !== fileInputs.length) {
        messageDiv.textContent = 'Number of titles should match the number of files.';
        messageDiv.style.display = 'block';
        messageDiv.style.color = 'red';
        return;
    }

    const formData = new FormData();
    
    titleInputs.forEach((input, index) => {
        formData.append(`titles`, input.value);
        formData.append(`prices`, priceInputs[index].value);
    });

    for (const file of fileInputs) {
        formData.append('files', file);
    }

    try {
        const response = await fetch('/add_images', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            messageDiv.textContent = result.message;
            messageDiv.style.display = 'block';
            messageDiv.style.color = 'green';
        } else {
            messageDiv.textContent = 'Submission failed. Please try again.';
            messageDiv.style.display = 'block';
            messageDiv.style.color = 'red';
        }
    } catch (error) {
        messageDiv.textContent = 'An error occurred. Please try again.';
        messageDiv.style.display = 'block';
        messageDiv.style.color = 'red';
    }
}
function createTitleInputs(files) {
    const container = document.getElementById('file-inputs-container');
    container.innerHTML = ''; // Clear previous inputs

    Array.from(files).forEach((file, index) => {
        const divWrapper = document.createElement('div'); // Create a div wrapper for each input

        const titleLabel = document.createElement('label');
        const priceLabel = document.createElement('label');
        titleLabel.textContent = `Title for ${file.name}:`; // Display filename in the label
        priceLabel.textContent = `Price for ${file.name}:`; // Display filename in the label

        const titleInput = document.createElement('input');
        const priceInput = document.createElement('input');

        titleInput.type = 'text';
        titleInput.name = `title_${index + 1}`;
        titleInput.required = true;

        priceInput.type = 'number';
        priceInput.name = `price_${index + 1}`;
        priceInput.required = true;

        divWrapper.appendChild(titleLabel);
        divWrapper.appendChild(titleInput);
        divWrapper.appendChild(priceLabel);
        divWrapper.appendChild(priceInput);

        container.appendChild(divWrapper);
    });
}

document.getElementById('add-file-upload').addEventListener('change', function() {
    const files = this.files;
    createTitleInputs(files);
});