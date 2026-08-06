(() => {
  const button = document.getElementById('pwa-install-button');
  if (!button || !('serviceWorker' in navigator)) return;

  let installPrompt = null;
  const standalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
  const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
  const isAndroid = /android/i.test(navigator.userAgent);
  const isDesktop = !isIOS && !isAndroid;
  const isMac = /macintosh|mac os x/i.test(navigator.userAgent);
  const isFirefox = /firefox/i.test(navigator.userAgent);

  const showMessage = options => {
    if (window.Swal) return window.Swal.fire(options);
    // Respaldo por si SweetAlert2 no pudo descargarse.
    window.alert(options.text || options.title);
    return Promise.resolve();
  };

  navigator.serviceWorker.register('/service-worker.js').catch(error => {
    console.error('No se pudo registrar el service worker:', error);
  });

  if (!standalone) button.hidden = false;

  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    installPrompt = event;
    button.hidden = false;
  });

  window.addEventListener('appinstalled', () => {
    installPrompt = null;
    button.hidden = true;
    showMessage({
      icon: 'success',
      title: 'Aplicación instalada',
      text: 'Mentor Consultorías ya está disponible en tu dispositivo.',
      confirmButtonText: 'Entendido',
      confirmButtonColor: '#5fcf80'
    });
  });

  button.addEventListener('click', async () => {
    if (installPrompt) {
      installPrompt.prompt();
      const choice = await installPrompt.userChoice;
      installPrompt = null;
      if (choice.outcome !== 'accepted') {
        showMessage({
          icon: 'info',
          title: 'Instalación cancelada',
          text: 'Puedes volver a instalar la aplicación cuando quieras usando este botón.',
          confirmButtonText: 'Entendido',
          confirmButtonColor: '#5fcf80'
        });
      }
      return;
    }
    if (isIOS) {
      showMessage({
        icon: 'info',
        title: 'Instalar en iPhone o iPad',
        html: 'Toca el botón <strong>Compartir</strong> <span aria-hidden="true">□↑</span> y selecciona <strong>Agregar a pantalla de inicio</strong>.',
        confirmButtonText: 'Entendido',
        confirmButtonColor: '#5fcf80'
      });
    } else if (isDesktop) {
      showMessage({
        icon: isFirefox ? 'warning' : 'info',
        title: isFirefox ? 'Firefox no permite instalarla en Fedora' : 'Instalar en esta computadora',
        html: isFirefox
          ? 'Abre esta página en <strong>Google Chrome, Chromium o Microsoft Edge</strong> y pulsa nuevamente <strong>Descargar / instalar</strong>.'
          : (isMac
            ? 'Usa <strong>Chrome o Edge</strong>, abre el menú del navegador y selecciona <strong>Instalar Mentor</strong>. En Safari compatible también puedes usar <strong>Archivo → Añadir al Dock</strong>.'
            : 'En Chrome o Chromium abre el menú <strong>⋮</strong>, entra en <strong>Transmitir, guardar y compartir</strong> y selecciona <strong>Instalar página como aplicación</strong>.'),
        footer: isFirefox ? 'En Fedora puedes instalar Chromium con: sudo dnf install chromium' : 'Mentor aparecerá en el menú de aplicaciones de tu computadora.',
        confirmButtonText: 'Entendido',
        confirmButtonColor: '#5fcf80'
      });
    } else {
      showMessage({
        icon: 'info',
        title: 'Instalar Mentor Consultorías',
        html: 'Abre el menú de tu navegador y elige <strong>Instalar aplicación</strong> o <strong>Agregar a pantalla de inicio</strong>.',
        confirmButtonText: 'Entendido',
        confirmButtonColor: '#5fcf80'
      });
    }
  });
})();
