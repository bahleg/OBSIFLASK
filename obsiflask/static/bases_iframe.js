  function setupIframeResize(iframe_id) {
    (function () {
      const iframe = document.getElementById(iframe_id);

      function resizeIframe() {
        try {
          const doc = iframe.contentDocument || iframe.contentWindow.document;
          if (doc && doc.body) {
            iframe.style.height = doc.body.scrollHeight + 'px';
          }
        } catch (e) {
          console.warn("Cannot access iframe (cross-origin)");
        }
      }

      iframe.addEventListener('load', () => {
        // Initial resize
        setTimeout(resizeIframe, 200);

        // Observe content changes
        try {
          const doc = iframe.contentDocument || iframe.contentWindow.document;
          if (doc && doc.body) {
            const observer = new MutationObserver(resizeIframe);
            observer.observe(doc.body, { childList: true, subtree: true });
          }
        } catch (e) {
          console.warn("Cannot observe iframe content (cross-origin)");
        }
      });
    })();
  }