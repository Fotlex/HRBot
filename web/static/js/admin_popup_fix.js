document.addEventListener('DOMContentLoaded', function() {
    
    function fixViewLinks() {
        const viewLinks = document.querySelectorAll('.view-related, .related-lookup');
        
        viewLinks.forEach(link => {
            if (link.getAttribute('href') && !link.dataset.popupFixed) {
                link.setAttribute('data-popup', 'yes');
                link.dataset.popupFixed = 'true';
                
                link.onclick = function(e) {
                    e.preventDefault();
                    if (typeof window.showRelatedObjectPopup === 'function') {
                        return showRelatedObjectPopup(this);
                    } else {
                        window.open(this.href, '_blank', 'width=1000,height=600,resizable=yes,scrollbars=yes');
                        return false;
                    }
                };
            }
        });
    }

    setTimeout(fixViewLinks, 500);

    const observer = new MutationObserver(function(mutations) {
        fixViewLinks();
    });

    observer.observe(document.body, { childList: true, subtree: true });
});