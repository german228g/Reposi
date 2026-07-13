const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
const isStandalone = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone;

export function initPWA() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js').catch(() => {});
  }

  const installBtn = document.getElementById('btn-install');
  const iosHint = document.getElementById('ios-hint');

  if (isStandalone) {
    installBtn?.remove();
    iosHint?.remove();
    return;
  }

  if (isIOS && installBtn) {
    installBtn.textContent = '📲 Добавить на экран Домой';
    installBtn.classList.remove('hidden');
    installBtn.addEventListener('click', () => {
      iosHint?.classList.toggle('visible');
    });
    return;
  }

  let deferredPrompt = null;
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    installBtn?.classList.remove('hidden');
  });

  installBtn?.addEventListener('click', async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
    installBtn.classList.add('hidden');
  });
}

export { isIOS, isStandalone };
