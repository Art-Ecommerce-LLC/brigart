document.addEventListener('DOMContentLoaded', (event) => {
    const container = document.getElementById('artworkContainer');
    let draggedItem = null;

    container.addEventListener('dragstart', (e) => {
        draggedItem = e.target;
        setTimeout(() => {
            e.target.style.display = 'none';
        }, 0);
    });

    container.addEventListener('dragend', (e) => {
        setTimeout(() => {
            draggedItem.style.display = 'block';
            draggedItem = null;
        }, 0);
    });

    container.addEventListener('dragover', (e) => {
        e.preventDefault();
    });

    container.addEventListener('dragenter', (e) => {
        e.preventDefault();
        if (e.target.classList.contains('artwork-item')) {
            e.target.style.border = '2px dashed #ccc';
        }
    });

    container.addEventListener('dragleave', (e) => {
        if (e.target.classList.contains('artwork-item')) {
            e.target.style.border = 'none';
        }
    });

    container.addEventListener('drop', (e) => {
        if (e.target.classList.contains('artwork-item')) {
            e.target.style.border = 'none';
            container.insertBefore(draggedItem, e.target);
        }
    });
});
