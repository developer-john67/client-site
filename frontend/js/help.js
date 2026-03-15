// Help page functionality

// WhatsApp chat feature
const whatsappBtn = document.getElementById('whatsappChatBtn');
if (whatsappBtn) {
    whatsappBtn.addEventListener('click', () => {
        // Replace with your actual WhatsApp number
        const phoneNumber = '1234567890';
        const message = encodeURIComponent('Hello! I need help with my order.');
        window.open(`https://wa.me/${phoneNumber}?text=${message}`, '_blank');
    });
}

// Contact form handling
const contactForm = document.getElementById('contactForm');
if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        // Get form data
        const formData = new FormData(contactForm);
        const data = Object.fromEntries(formData);
        
        // In a real app, you would send this to a server
        console.log('Contact form submitted:', data);
        
        // Show success message
        alert('Thank you for your message! We will get back to you soon.');
        contactForm.reset();
    });
}

// FAQ accordion functionality
function initializeFAQ() {
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        const answer = item.querySelector('.faq-answer');
        
        // Initially hide answers
        if (answer) {
            answer.style.display = 'none';
        }
        
        question.addEventListener('click', () => {
            // Toggle answer visibility
            if (answer.style.display === 'none') {
                answer.style.display = 'block';
                question.querySelector('i').classList.replace('fa-chevron-down', 'fa-chevron-up');
            } else {
                answer.style.display = 'none';
                question.querySelector('i').classList.replace('fa-chevron-up', 'fa-chevron-down');
            }
        });
    });
}

// Help card interactions
function initializeHelpCards() {
    const helpCards = document.querySelectorAll('.help-card');
    
    helpCards.forEach(card => {
        card.addEventListener('click', () => {
            const topic = card.querySelector('h3').textContent;
            // In a real app, you would navigate to specific help topic
            alert(`Opening ${topic} help section...`);
        });
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeFAQ();
    initializeHelpCards();
    
    // Update cart count from localStorage
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    const cartCount = document.querySelector('.cart-count');
    if (cartCount) {
        const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
        cartCount.textContent = totalItems;
    }
});