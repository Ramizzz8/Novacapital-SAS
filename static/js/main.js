// Funciones globales reutilizables

// Formatear moneda colombiana
function formatCurrency(value) {
  return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
  }).format(value);
}

// Validar número de documento
function validateDocument(type, number) {
  const patterns = {
      'CC': /^\d{6,10}$/,
      'CE': /^\d{6,10}$/,
      'TI': /^\d{10,11}$/,
      'PP': /^[A-Z0-9]{6,10}$/
  };
  return patterns[type]?.test(number) || false;
}

// Validar email
function validateEmail(email) {
  const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return pattern.test(email);
}

// Validar teléfono colombiano
function validatePhone(phone) {
  const pattern = /^3\d{9}$/;
  return pattern.test(phone.replace(/\s/g, ''));
}

// Mostrar notificación
function showNotification(message, type = 'info') {
  // Implementar sistema de notificaciones
  alert(message);
}
