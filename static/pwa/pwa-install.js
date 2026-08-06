(() => {
  const button = document.getElementById('pwa-install-button');
  if (!button || !('serviceWorker' in navigator)) return;

  let installPrompt = null;
  const standalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
  const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
  const isDesktop = !/android|iphone|ipad|ipod|mobile/i.test(navigator.userAgent);
  const isMac = /macintosh|mac os x/i.test(navigator.userAgent);

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
        icon: 'info',
        title: 'Instalar en esta computadora',
        html: isMac
          ? 'Usa <strong>Chrome o Edge</strong>, abre el menú del navegador y selecciona <strong>Instalar Mentor</strong>. En Safari compatible también puedes usar <strong>Archivo → Añadir al Dock</strong>.'
          : 'Usa <strong>Google Chrome o Microsoft Edge</strong>, abre el menú <strong>⋮</strong> y selecciona <strong>Instalar Mentor</strong> o <strong>Aplicaciones → Instalar este sitio como una aplicación</strong>.',
        footer: 'La aplicación se abrirá en su propia ventana y aparecerá en el menú de aplicaciones.',
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
