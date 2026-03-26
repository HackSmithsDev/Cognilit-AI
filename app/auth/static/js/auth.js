$(document).ready(function() {

    // --- 1. VIEW CONTROLLER ---
    // Handles toggling between Sign-in, Sign-up, and Forgot Password boxes
    function switchAuthBox(targetId, subtitle) {
        $('.auth-box').addClass('d-none');
        $(`#${targetId}`).removeClass('d-none');
        
        if (subtitle) {
            $('#auth-subtitle').text(subtitle);
        } else {
            // Default subtitles
            const defaults = {
                'signin-box': 'Welcome back! Please sign in.',
                'signup-box-1': 'Join us today! Create your account.',
                'signup-box-2': 'Tell us a bit about yourself.',
                'forgot-box': 'Reset your password.',
                'verify-box': 'Check your inbox.',
                'reset-box': 'Choose a new password.'
            };
            $('#auth-subtitle').text(defaults[targetId] || 'Access your research vault.');
        }
    }

    $('.switch-box').on('click', function(e) {
        e.preventDefault();
        const target = $(this).data('target');
        // Reset signup to step 1 if navigating to it
        switchAuthBox(target === 'signup-box' ? 'signup-box-1' : target);
    });


    // --- 2. MULTI-STEP REGISTRATION ---
    
    // Step 1: Email & Password Validation
    $('#btn-signup-next').on('click', function() {
        const email = $('#signup-email').val();
        const pass = $('#signup-password').val();
        const confirm = $('#signup-password-confirm').val();

        if (!email || !pass || pass !== confirm) {
            alert("Please ensure passwords match and email is valid.");
            return;
        }

        // Check if email is available before proceeding to Step 2
        $.ajax({
            url: '/auth/check-email',
            type: 'GET',
            data: { email: email },
            success: function(response) {
                if (response.exists) {
                    alert("This email is already registered. Please sign in.");
                } else {
                    switchAuthBox('signup-box-2');
                }
            },
            error: function() {
                alert('Communication error. Please try again.');
            }
        });
    });

    $('#btn-signup-back').on('click', function() {
        switchAuthBox('signup-box-1');
    });

    // Final Submission: Profile Details
    $('#form-signup-final').on('submit', function(e) {
        e.preventDefault();

        const urlParams = new URLSearchParams(window.location.search);
        const nextParam = urlParams.get('next');
        const ajaxUrl = nextParam ? `/auth/signup?next=${encodeURIComponent(nextParam)}` : '/auth/signup';

        const signupData = {
            email: $('#signup-email').val(),
            password: $('#signup-password').val(),
            first_name: $('#signup-fname').val(),
            last_name: $('#signup-lname').val(),
            age: parseInt($('#signup-age').val()),
            gender: $('#signup-gender').val(),
            profession: $('#signup-profession').val()
        };

        $.ajax({
            url: ajaxUrl,
            type: 'POST',
            data: JSON.stringify(signupData),
            contentType: 'application/json',
            success: function(response) {
                if (response.status === "success") {
                    window.location.href = response.redirect;
                }
            },
            error: function(xhr) {
                const errorMsg = xhr.responseJSON ? xhr.responseJSON.message : "Signup failed";
                alert(errorMsg);
            }
        });
    });


    // --- 3. PASSWORD RECOVERY (REDIS BACKED) ---

    // A. Request Reset Code
    $('#form-forgot').on('submit', function(e) {
        e.preventDefault();
        const email = $('#forgot-email').val();
        
        $.ajax({
            url: '/auth/forget_password',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ email: email }),
            success: function() {
                switchAuthBox('verify-box', 'Check your inbox for the 6-digit code.');
            },
            error: function() { 
                alert("Error sending reset code."); 
            }
        });
    });

    // B. Verify OTP (Automatic trigger on 6th digit)
    $('#otp-single').on('input', function() {
        this.value = this.value.replace(/[^0-9]/g, '');
        
        if (this.value.length === 6) {
            const otpData = {
                email: $('#forgot-email').val(),
                otp: $(this).val()
            };

            $.ajax({
                url: '/auth/verify_otp',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(otpData),
                success: function() {
                    switchAuthBox('reset-box', 'Create your new password.');
                },
                error: function(xhr) {
                    alert(xhr.responseJSON.message || "Invalid Code");
                    $('#otp-single').val(''); // Clear on failure
                }
            });
        }
    });

    // C. Update Password
    $('#form-reset').on('submit', function(e) {
        e.preventDefault();
        const pass = $('#new-password').val();
        const confirm = $('#confirm-password').val();

        if (pass !== confirm) {
            alert("Passwords do not match.");
            return;
        }

        const resetData = {
            email: $('#forgot-email').val(),
            otp: $('#otp-single').val(),
            password: pass
        };

        $.ajax({
            url: '/auth/reset_password',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(resetData),
            success: function() {
                alert("Password updated! Please sign in.");
                switchAuthBox('signin-box');
            },
            error: function(xhr) { 
                alert(xhr.responseJSON.message || "Reset failed."); 
            }
        });
    });


    // --- 4. SIGN IN SUBMISSION ---
    $('#form-signin').on('submit', function(e) {
        e.preventDefault();
        // Add your sign-in AJAX here similar to signup if needed
        // Get 'next' parameter from the current URL bar
        const urlParams = new URLSearchParams(window.location.search);
        const nextParam = urlParams.get('next');
        const ajaxUrl = nextParam ? `/auth/login?next=${encodeURIComponent(nextParam)}` : '/auth/login';

        const loginData = {
            email: $('#signin-email').val(),
            password: $('#signin-password').val()
        };
        
        $.ajax({
            url:  ajaxUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(loginData),
            success: function(response) {
                if (response.status === "success") {
                    window.location.href = response.redirect;
                }
            },
            error: function() { alert("Invalid credentials."); }
        });
    });

});