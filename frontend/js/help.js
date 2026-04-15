// Help page functionality

// Help card click handlers - navigate to sections
document.querySelectorAll('.help-card').forEach(card => {
    card.addEventListener('click', () => {
        const topic = card.querySelector('h3').textContent;
        
        // Scroll to appropriate section based on topic
        if (topic.includes('Shipping')) {
            window.location.href = '#shipping-info';
        } else if (topic.includes('Returns')) {
            window.location.href = '#returns-info';
        } else if (topic.includes('Payment')) {
            window.location.href = '#payment-info';
        } else {
            window.location.href = '#faq-section';
        }
    });
});
