const { clearFirestoreData } = require("@firebase/rules-unit-testing");

module.exports = async () => {
  // No se limpia en teardown global para permitir inspección post-test.
  // Usa el método clearAndResetFirestoreEmulator() por suite si es necesario.
};
