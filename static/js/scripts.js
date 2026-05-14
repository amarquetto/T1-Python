/**
 * scripts.js — JavaScript do PataFeliz PetShop
 *
 * Funcionalidades:
 *  1. Confirmação de exclusão com modal Bootstrap
 *  2. Indicador de força de senha no cadastro
 *  3. Validação de confirmação de senha em tempo real
 *  4. Toggle de visibilidade da senha
 */

/* ─────────────────────────────────────────────────────
   1. CONFIRMAÇÃO DE EXCLUSÃO
   Chamado pelo atributo onclick nos botões de excluir.
   Exibe caixa de confirmação nativa do navegador.
───────────────────────────────────────────────────── */
function confirmarExclusao(nomeItem) {
  return window.confirm(
    `⚠️ Deseja realmente excluir "${nomeItem}"?\n\nEsta ação não poderá ser desfeita.`
  );
}

/** Uso: <form onsubmit="return confirmarExclusaoSubmit(event, 'Nome')"> — envia POST ao Flask se confirmar. */
function confirmarExclusaoSubmit(event, nomeItem) {
  if (!confirmarExclusao(nomeItem)) {
    event.preventDefault();
    return false;
  }
  return true;
}

/* ─────────────────────────────────────────────────────
   2. INDICADOR DE FORÇA DE SENHA
   Atualiza a barra de progresso e o texto de feedback
   conforme o usuário digita a senha.
───────────────────────────────────────────────────── */
function verificarForcaSenha(senha) {
  const barra  = document.getElementById('barraSenha');
  const texto  = document.getElementById('textoForcaSenha');

  if (!barra || !texto) return; // Só executa na página de cadastro

  let pontos = 0;

  // Critérios de avaliação da senha
  if (senha.length >= 6)                      pontos++; // comprimento mínimo
  if (senha.length >= 10)                     pontos++; // comprimento bom
  if (/[A-Z]/.test(senha))                    pontos++; // letra maiúscula
  if (/[0-9]/.test(senha))                    pontos++; // número
  if (/[^A-Za-z0-9]/.test(senha))            pontos++; // caractere especial

  // Mapeamento de pontos para estilo e mensagem
  const niveis = [
    { min: 0, max: 0,  cor: '',         pct: 0,   msg: '',                      classe: 'text-muted'    },
    { min: 1, max: 1,  cor: 'bg-danger',pct: 20,  msg: '😟 Muito fraca',         classe: 'text-danger'   },
    { min: 2, max: 2,  cor: 'bg-warning',pct:40,  msg: '😐 Fraca',               classe: 'text-warning'  },
    { min: 3, max: 3,  cor: 'bg-info',  pct: 60,  msg: '🙂 Razoável',            classe: 'text-info'     },
    { min: 4, max: 4,  cor: 'bg-primary',pct:80,  msg: '😊 Boa',                 classe: 'text-primary'  },
    { min: 5, max: 5,  cor: 'bg-success',pct:100, msg: '💪 Muito forte!',         classe: 'text-success'  },
  ];

  const nivel = niveis.find(n => pontos >= n.min && pontos <= n.max) || niveis[0];

  // Atualiza a barra de progresso
  barra.style.width    = nivel.pct + '%';
  barra.className      = 'progress-bar ' + nivel.cor;

  // Atualiza o texto de feedback
  texto.textContent    = nivel.msg;
  texto.className      = 'form-text ' + nivel.classe;
}

/* ─────────────────────────────────────────────────────
   3. VALIDAÇÃO DE CONFIRMAÇÃO DE SENHA EM TEMPO REAL
   Compara os campos de senha e confirmação e exibe
   feedback visual imediato ao usuário.
───────────────────────────────────────────────────── */
function configurarValidacaoConfirmacao() {
  const campoSenha    = document.getElementById('senha');
  const campoConfirm  = document.getElementById('confirmar_senha');
  const feedback      = document.getElementById('feedbackConfirmacao');

  if (!campoSenha || !campoConfirm || !feedback) return;

  function verificar() {
    if (!campoConfirm.value) {
      feedback.textContent = '';
      campoConfirm.classList.remove('is-valid', 'is-invalid');
      return;
    }

    if (campoSenha.value === campoConfirm.value) {
      feedback.textContent  = '✅ Senhas coincidem!';
      feedback.className    = 'form-text text-success';
      campoConfirm.classList.add('is-valid');
      campoConfirm.classList.remove('is-invalid');
    } else {
      feedback.textContent  = '❌ As senhas não coincidem.';
      feedback.className    = 'form-text text-danger';
      campoConfirm.classList.add('is-invalid');
      campoConfirm.classList.remove('is-valid');
    }
  }

  // Verifica ao digitar em ambos os campos
  campoSenha.addEventListener('input',   verificar);
  campoConfirm.addEventListener('input', verificar);
}

/* ─────────────────────────────────────────────────────
   4. TOGGLE DE VISIBILIDADE DE SENHA
   Alterna entre tipo "password" e "text" no campo de
   senha do login, com ícone correspondente.
───────────────────────────────────────────────────── */
function configurarToggleSenha() {
  const botao  = document.getElementById('toggleSenha');
  const campo  = document.getElementById('senha');
  const icone  = document.getElementById('iconeSenha');

  if (!botao || !campo || !icone) return;

  botao.addEventListener('click', function () {
    const visivel = campo.type === 'text';
    campo.type    = visivel ? 'password' : 'text';
    icone.className = visivel ? 'bi bi-eye' : 'bi bi-eye-slash';
    botao.setAttribute('title', visivel ? 'Exibir senha' : 'Ocultar senha');
  });
}

/* ─────────────────────────────────────────────────────
   INICIALIZAÇÃO
   Executa ao carregar o DOM da página.
───────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
  configurarValidacaoConfirmacao();
  configurarToggleSenha();

  // Fecha os alertas de flash automaticamente após 5 segundos
  const alertas = document.querySelectorAll('.alert.alert-dismissible');
  alertas.forEach(function (alerta) {
    setTimeout(function () {
      const instancia = bootstrap.Alert.getOrCreateInstance(alerta);
      instancia.close();
    }, 5000);
  });
});
