import { ProfileManager } from './auth/profileManager.js';
import { initFlashMessages } from './auth/authFlash.js';
import { debounce, initFormUtils } from './core/formUtils.js';
import { initUIUtils } from './core/uiUtils.js';

// Inicialização quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
  // Mensagens flash
  initFlashMessages();

  // Gerenciador de perfil
  if (document.getElementById('formEditarPerfil')) {
    new ProfileManager();
  }

  // Utilitários
  initFormUtils();
  initUIUtils();

  // Exemplo de uso do debounce
  window.addEventListener('resize', debounce(() => {
    console.log('Resized');
  }));
});

// Inicializa máscaras quando jQuery estiver pronto
$(document).ready(() => {
  $('.cpf-mask').mask('000.000.000-00');
});