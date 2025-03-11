document.addEventListener('DOMContentLoaded', function() {
    const loginBtn = document.getElementById('loginBtn');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');

    loginBtn.addEventListener('click', function() {
        // Validate inputs
        if (!usernameInput.value.trim()) {
            alert('Please enter your username');
            usernameInput.focus();
            return;
        }

        if (!passwordInput.value.trim()) {
            alert('Please enter your password');
            passwordInput.focus();
            return;
        }

        // Here you would typically make an API call to your backend for authentication
        // For demonstration purposes, we're just showing an alert
        alert('Login attempt with username: ' + usernameInput.value);
        
        // In a real application, you would handle the login response here
        // Example:
        // fetch('/api/login', {
        //     method: 'POST',
        //     headers: {
        //         'Content-Type': 'application/json',
        //     },
        //     body: JSON.stringify({
        //         username: usernameInput.value,
        //         password: passwordInput.value
        //     })
        // })
        // .then(response => response.json())
        // .then(data => {
        //     if (data.success) {
        //         window.location.href = '/dashboard.html';
        //     } else {
        //         alert('Login failed: ' + data.message);
        //     }
        // })
        // .catch(error => {
        //     console.error('Error:', error);
        //     alert('An error occurred during login');
        // });
    });
});