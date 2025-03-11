document.addEventListener('DOMContentLoaded', function() {
    const resetBtn = document.getElementById('resetBtn');
    const getOtpBtn = document.getElementById('getOtpBtn');
    const usernameInput = document.getElementById('username');
    const newPasswordInput = document.getElementById('newPassword');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const otpInput = document.getElementById('otpInput');

    getOtpBtn.addEventListener('click', function() {
        if (!usernameInput.value.trim()) {
            alert('Please enter your username to receive OTP');
            usernameInput.focus();
            return;
        }

        // Simulate OTP generation
        alert('OTP sent to your registered email/phone for username: ' + usernameInput.value);
        
        // In a real application, you would make an API call to your backend
        // to send an OTP to the user's registered email or phone
    });

    resetBtn.addEventListener('click', function() {
        // Validate inputs
        if (!usernameInput.value.trim()) {
            alert('Please enter your username');
            usernameInput.focus();
            return;
        }

        if (!newPasswordInput.value.trim()) {
            alert('Please enter a new password');
            newPasswordInput.focus();
            return;
        }

        if (newPasswordInput.value !== confirmPasswordInput.value) {
            alert('Passwords do not match');
            confirmPasswordInput.focus();
            return;
        }

        if (!otpInput.value.trim()) {
            alert('Please enter the OTP sent to your registered email/phone');
            otpInput.focus();
            return;
        }

        // Here you would typically make an API call to your backend to reset the password
        // For demonstration purposes, we're just showing an alert
        alert('Password reset attempt for username: ' + usernameInput.value);
        
        // In a real application, you would handle the password reset response here
        // Example:
        // fetch('/api/reset-password', {
        //     method: 'POST',
        //     headers: {
        //         'Content-Type': 'application/json',
        //     },
        //     body: JSON.stringify({
        //         username: usernameInput.value,
        //         newPassword: newPasswordInput.value,
        //         otp: otpInput.value
        //     })
        // })
        // .then(response => response.json())
        // .then(data => {
        //     if (data.success) {
        //         alert('Password reset successful!');
        //         window.location.href = '/index.html';
        //     } else {
        //         alert('Password reset failed: ' + data.message);
        //     }
        // })
        // .catch(error => {
        //     console.error('Error:', error);
        //     alert('An error occurred during password reset');
        // });
    });
});