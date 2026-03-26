/**
 * theme.js - Logic for theme switching and OS preference syncing
 */
function getSystemTheme() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

$(document).ready(function() {
    const $html = $('html');
    const $themeToggle = $('#theme-toggle');
    const $themeIcon = $themeToggle.find('i');

    function applyThemeUI(theme, mode) {
        $html.attr('data-bs-theme', theme);
        if (mode) $html.attr('data-theme-mode', mode);

        if (theme === 'dark') {
            $themeIcon.removeClass('bi-moon-stars').addClass('bi-sun-fill');
        } else {
            $themeIcon.removeClass('bi-sun-fill').addClass('bi-moon-stars');
        }
    }

    // sync the icon with what the inline script already did to the <html> tag
    applyThemeUI($html.attr('data-bs-theme'));

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
        if ($html.attr('data-theme-mode') === 'auto') {
            applyThemeUI(event.matches ? "dark" : "light");
        }
    });

    $themeToggle.on('click', function() {
        const currentTheme = $html.attr('data-bs-theme');
        const newTheme = (currentTheme === 'light') ? 'dark' : 'light';
        
        $('body, html').addClass('no-transition');

        applyThemeUI(newTheme, newTheme);

        setTimeout(() => $('body').removeClass('no-transition'), 300);

        // Persist to Backend - CHECK YOUR BLUEPRINT PREFIX HERE
        $.ajax({
            url: '/setting/update-theme', 
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ theme: newTheme.charAt(0).toUpperCase() + newTheme.slice(1) }),
            success: (res) => console.log("Theme synced:", res.theme),
            error: (err) => console.error("Sync error. Check if URL is /setting/ or /settings/", err)
        });
    });
});