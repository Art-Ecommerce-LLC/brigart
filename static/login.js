async function login() {
    const form = document.getElementById('login-form');
    const errorMessage = document.getElementById('error-message');

    const formData = new FormData(form);
    const data = {
        username: formData.get('username'),
        password: formData.get('password')
    };

    const response = await fetch('/credentials_check', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });

    if (response.status === 201) {
        // Redirect to portal or other page on successful login
        window.location.href = '/logs';
    }
    else if (response.status === 200) {
        window.location.href = '/brig_portal';
    }
     else {
        // Show error message on failed login
        errorMessage.style.display = 'block';
    }
}