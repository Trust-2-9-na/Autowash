document.addEventListener('DOMContentLoaded', function () {
    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(function (link) {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Toggle hidden pages
    const menuButton = document.getElementById('menuButton');
    const hiddenPages = document.getElementById('hiddenPages');
    menuButton.addEventListener('click', function () {
        hiddenPages.classList.toggle('show');
    });
});
