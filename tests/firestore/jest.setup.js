// Verifica que el emulador de Firestore esté corriendo
// Ejecutar antes de las pruebas: firebase emulators:start --only firestore,auth

module.exports = async () => {
  process.env.FIRESTORE_EMULATOR_HOST = process.env.FIRESTORE_EMULATOR_HOST || "localhost:8080";
  process.env.FIREBASE_AUTH_EMULATOR_HOST = process.env.FIREBASE_AUTH_EMULATOR_HOST || "localhost:9099";
};
