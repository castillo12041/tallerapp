/**
 * Tests de Firestore Security Rules
 * Proyecto: taller-85514
 *
 * Prerrequisitos:
 *   firebase emulators:start --only firestore,auth
 *
 * Ejecutar:
 *   cd tests/firestore && npm test
 */

const {
  initializeTestEnvironment,
  assertFails,
  assertSucceeds,
} = require("@firebase/rules-unit-testing");
const fs = require("fs");
const path = require("path");

const PROJECT_ID = "taller-85514";
const RULES_PATH = path.resolve(__dirname, "../../infra/firebase/firestore.rules");

// ============================================================================
// Setup
// ============================================================================

let testEnv;

beforeAll(async () => {
  testEnv = await initializeTestEnvironment({
    projectId: PROJECT_ID,
    firestore: {
      rules: fs.readFileSync(RULES_PATH, "utf8"),
      host: "localhost",
      port: 8080,
    },
  });
});

afterEach(async () => {
  await testEnv.clearFirestore();
});

afterAll(async () => {
  await testEnv.cleanup();
});

// ============================================================================
// Helpers
// ============================================================================

function unauthContext() {
  return testEnv.unauthenticatedContext();
}

function authContext(uid, customClaims = {}) {
  return testEnv.authenticatedContext(uid, customClaims);
}

function superAdminContext(uid = "superadmin-uid") {
  return authContext(uid, { role: "superadmin", tenantId: null, permissions: ["*"] });
}

function tenantUserContext(uid, tenantId, role, permissions = []) {
  return authContext(uid, { role, tenantId, permissions });
}

function inspectorContext(uid, tenantId) {
  return tenantUserContext(uid, tenantId, "inspector", [
    "clients:read", "vehicles:read", "vehicles:create",
    "inspections:read", "inspections:create", "inspections:update", "inspections:complete",
    "calendar:read", "dashboard:read", "pdf:generate",
  ]);
}

function tenantAdminContext(uid, tenantId) {
  return tenantUserContext(uid, tenantId, "tenantadmin", [
    "users:read", "users:create", "users:update", "users:delete",
    "roles:manage", "tenant:read", "tenant:manage",
    "clients:read", "clients:create", "clients:update", "clients:delete",
    "vehicles:read", "vehicles:create", "vehicles:update", "vehicles:delete",
    "inspections:read", "inspections:create", "inspections:update",
    "inspections:complete", "inspections:assign", "inspections:review",
    "templates:manage", "estimates:read", "estimates:create", "estimates:update",
    "estimates:send", "estimates:convert", "work_orders:read", "work_orders:create",
    "work_orders:update", "work_orders:complete", "calendar:read", "calendar:create",
    "calendar:update", "calendar:delete", "dashboard:read", "reports:read",
    "reports:export", "notifications:manage", "audit:read",
    "api_keys:manage", "webhooks:manage", "pdf:generate", "qr:generate",
  ]);
}

async function seedDoc(collection, id, data) {
  await testEnv.withSecurityRulesDisabled(async (ctx) => {
    await ctx.firestore().collection(collection).doc(id).set(data);
  });
}

// ============================================================================
// Colección: plans (global)
// ============================================================================

describe("plans — Planes SaaS globales", () => {
  const PLAN = { code: "basic", name: "Basic", features: {} };

  beforeEach(async () => {
    await seedDoc("plans", "basic", PLAN);
  });

  test("usuario no autenticado NO puede leer planes", async () => {
    const db = unauthContext().firestore();
    await assertFails(db.collection("plans").doc("basic").get());
  });

  test("usuario autenticado SÍ puede leer planes", async () => {
    const db = authContext("user-1", { role: "inspector", tenantId: "tenant-1", permissions: [] }).firestore();
    await assertSucceeds(db.collection("plans").doc("basic").get());
  });

  test("usuario normal NO puede escribir planes", async () => {
    const db = authContext("user-1", { role: "tenantadmin", tenantId: "tenant-1", permissions: [] }).firestore();
    await assertFails(db.collection("plans").doc("pro").set({ code: "pro" }));
  });

  test("superadmin SÍ puede escribir planes", async () => {
    const db = superAdminContext().firestore();
    await assertSucceeds(db.collection("plans").doc("pro").set({ code: "pro", name: "Pro", features: {} }));
  });
});

// ============================================================================
// Colección: tenants
// ============================================================================

describe("tenants — Aislamiento de tenants", () => {
  const TENANT_A = { name: "Taller A", planId: "basic", tenantId: "tenant-a" };
  const TENANT_B = { name: "Taller B", planId: "basic", tenantId: "tenant-b" };

  beforeEach(async () => {
    await seedDoc("tenants", "tenant-a", TENANT_A);
    await seedDoc("tenants", "tenant-b", TENANT_B);
  });

  test("usuario de tenant-a SÍ puede leer su propio tenant", async () => {
    const db = tenantAdminContext("user-a", "tenant-a").firestore();
    await assertSucceeds(db.collection("tenants").doc("tenant-a").get());
  });

  test("usuario de tenant-a NO puede leer tenant-b", async () => {
    const db = tenantAdminContext("user-a", "tenant-a").firestore();
    await assertFails(db.collection("tenants").doc("tenant-b").get());
  });

  test("superadmin SÍ puede leer cualquier tenant", async () => {
    const db = superAdminContext().firestore();
    await assertSucceeds(db.collection("tenants").doc("tenant-a").get());
    await assertSucceeds(db.collection("tenants").doc("tenant-b").get());
  });

  test("usuario no autenticado NO puede leer tenants", async () => {
    const db = unauthContext().firestore();
    await assertFails(db.collection("tenants").doc("tenant-a").get());
  });

  test("solo superadmin puede CREAR tenants", async () => {
    const db = tenantAdminContext("user-a", "tenant-a").firestore();
    await assertFails(db.collection("tenants").doc("tenant-new").set({ name: "Nuevo", tenantId: "tenant-a" }));
  });

  test("superadmin SÍ puede crear tenants", async () => {
    const db = superAdminContext().firestore();
    await assertSucceeds(db.collection("tenants").doc("tenant-new").set({ name: "Nuevo", tenantId: "tenant-new", planId: "basic" }));
  });
});

// ============================================================================
// Colección: clients — Aislamiento de datos de clientes
// ============================================================================

describe("clients — Aislamiento por tenant", () => {
  const CLIENT_A = { name: "Cliente A", tenantId: "tenant-a", createdAt: new Date(), updatedAt: new Date(), createdBy: "u1", updatedBy: "u1" };
  const CLIENT_B = { name: "Cliente B", tenantId: "tenant-b", createdAt: new Date(), updatedAt: new Date(), createdBy: "u2", updatedBy: "u2" };

  beforeEach(async () => {
    await seedDoc("clients", "client-a", CLIENT_A);
    await seedDoc("clients", "client-b", CLIENT_B);
  });

  test("inspector de tenant-a SÍ puede leer clientes de tenant-a", async () => {
    const db = inspectorContext("user-a", "tenant-a").firestore();
    await assertSucceeds(db.collection("clients").doc("client-a").get());
  });

  test("inspector de tenant-a NO puede leer clientes de tenant-b", async () => {
    const db = inspectorContext("user-a", "tenant-a").firestore();
    await assertFails(db.collection("clients").doc("client-b").get());
  });

  test("inspector NO puede crear clientes (no tiene clients:create)", async () => {
    const db = inspectorContext("user-a", "tenant-a").firestore();
    await assertFails(
      db.collection("clients").doc("client-new").set({
        name: "Nuevo",
        tenantId: "tenant-a",
        createdAt: new Date(),
        updatedAt: new Date(),
        createdBy: "user-a",
        updatedBy: "user-a",
      })
    );
  });

  test("recepcionista SÍ puede crear clientes en su tenant", async () => {
    const db = tenantUserContext("recep-a", "tenant-a", "receptionist", [
      "clients:read", "clients:create", "clients:update",
      "vehicles:read", "vehicles:create", "vehicles:update",
      "inspections:read", "inspections:create",
    ]).firestore();

    await assertSucceeds(
      db.collection("clients").doc("client-new").set({
        name: "Nuevo",
        tenantId: "tenant-a",
        createdAt: new Date(),
        updatedAt: new Date(),
        createdBy: "recep-a",
        updatedBy: "recep-a",
      })
    );
  });

  test("recepcionista NO puede crear cliente con tenantId de otro tenant", async () => {
    const db = tenantUserContext("recep-a", "tenant-a", "receptionist", [
      "clients:create",
    ]).firestore();

    await assertFails(
      db.collection("clients").doc("infiltrado").set({
        name: "Infiltrado",
        tenantId: "tenant-b",  // ← Cross-tenant injection
        createdAt: new Date(),
        updatedAt: new Date(),
        createdBy: "recep-a",
        updatedBy: "recep-a",
      })
    );
  });
});

// ============================================================================
// Colección: notifications — cada usuario solo ve las suyas
// ============================================================================

describe("notifications — Aislamiento por usuario", () => {
  const NOTIF_A = {
    userId: "user-a",
    tenantId: "tenant-a",
    read: false,
    message: "Tu inspección está lista",
    createdAt: new Date(),
    updatedAt: new Date(),
    createdBy: "system",
    updatedBy: "system",
  };
  const NOTIF_B = {
    userId: "user-b",
    tenantId: "tenant-a",
    read: false,
    message: "Tu inspección está lista",
    createdAt: new Date(),
    updatedAt: new Date(),
    createdBy: "system",
    updatedBy: "system",
  };

  beforeEach(async () => {
    await seedDoc("notifications", "notif-a", NOTIF_A);
    await seedDoc("notifications", "notif-b", NOTIF_B);
  });

  test("user-a SÍ puede leer su propia notificación", async () => {
    const db = inspectorContext("user-a", "tenant-a").firestore();
    await assertSucceeds(db.collection("notifications").doc("notif-a").get());
  });

  test("user-a NO puede leer la notificación de user-b", async () => {
    const db = inspectorContext("user-a", "tenant-a").firestore();
    await assertFails(db.collection("notifications").doc("notif-b").get());
  });

  test("user-a SÍ puede marcar como leída su notificación", async () => {
    const db = inspectorContext("user-a", "tenant-a").firestore();
    await assertSucceeds(
      db.collection("notifications").doc("notif-a").update({
        read: true,
        readAt: new Date(),
        updatedAt: new Date(),
      })
    );
  });

  test("user-a NO puede crear notificaciones (solo backend)", async () => {
    const db = inspectorContext("user-a", "tenant-a").firestore();
    await assertFails(
      db.collection("notifications").doc("notif-new").set({
        userId: "user-a",
        tenantId: "tenant-a",
        read: false,
        message: "Hacked",
        createdAt: new Date(),
        updatedAt: new Date(),
        createdBy: "user-a",
        updatedBy: "user-a",
      })
    );
  });
});

// ============================================================================
// Colección: audit_logs — solo lectura, solo backend puede escribir
// ============================================================================

describe("audit_logs — Solo backend puede escribir", () => {
  const LOG = {
    tenantId: "tenant-a",
    userId: "user-a",
    action: "CREATE",
    entityType: "inspection",
    entityId: "insp-123",
    createdAt: new Date(),
    updatedAt: new Date(),
    createdBy: "user-a",
    updatedBy: "user-a",
  };

  beforeEach(async () => {
    await seedDoc("audit_logs", "log-1", LOG);
  });

  test("tenantadmin SÍ puede leer logs de su tenant", async () => {
    const db = tenantAdminContext("admin-a", "tenant-a").firestore();
    await assertSucceeds(db.collection("audit_logs").doc("log-1").get());
  });

  test("inspector NO puede leer audit logs (sin permiso)", async () => {
    const db = inspectorContext("user-a", "tenant-a").firestore();
    await assertFails(db.collection("audit_logs").doc("log-1").get());
  });

  test("ningún cliente puede CREAR audit logs", async () => {
    const db = tenantAdminContext("admin-a", "tenant-a").firestore();
    await assertFails(
      db.collection("audit_logs").doc("fake-log").set({
        tenantId: "tenant-a",
        userId: "admin-a",
        action: "HACKED",
        entityType: "audit_logs",
        entityId: "fake",
        createdAt: new Date(),
        updatedAt: new Date(),
        createdBy: "admin-a",
        updatedBy: "admin-a",
      })
    );
  });
});

// ============================================================================
// Colección: public_tokens — lectura pública, escritura solo backend
// ============================================================================

describe("public_tokens — Tokens públicos", () => {
  const TOKEN = {
    type: "inspection_report",
    tenantId: "tenant-a",
    entityId: "insp-123",
    hmac: "sha256-hash",
    expiresAt: new Date(Date.now() + 86400000),
    revokedAt: null,
    createdAt: new Date(),
    updatedAt: new Date(),
    createdBy: "system",
    updatedBy: "system",
  };

  beforeEach(async () => {
    await seedDoc("public_tokens", "token-1", TOKEN);
  });

  test("usuario no autenticado SÍ puede leer tokens públicos", async () => {
    const db = unauthContext().firestore();
    await assertSucceeds(db.collection("public_tokens").doc("token-1").get());
  });

  test("usuario autenticado SÍ puede leer tokens públicos", async () => {
    const db = inspectorContext("user-a", "tenant-a").firestore();
    await assertSucceeds(db.collection("public_tokens").doc("token-1").get());
  });

  test("NADIE puede escribir tokens públicos desde el cliente", async () => {
    const db = superAdminContext().firestore();
    await assertFails(
      db.collection("public_tokens").doc("forged").set({
        type: "inspection_report",
        tenantId: "tenant-a",
        entityId: "insp-123",
        hmac: "forged",
        expiresAt: new Date(Date.now() + 999999999),
        revokedAt: null,
        createdAt: new Date(),
        updatedAt: new Date(),
        createdBy: "attacker",
        updatedBy: "attacker",
      })
    );
  });
});

// ============================================================================
// Colección: users — protección de campos sensibles
// ============================================================================

describe("users — Protección de rol y tenantId", () => {
  const USER_A = {
    uid: "user-a",
    email: "user@taller-a.cl",
    tenantId: "tenant-a",
    role: "inspector",
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date(),
    createdBy: "admin-a",
    updatedBy: "admin-a",
  };

  beforeEach(async () => {
    await seedDoc("users", "user-a", USER_A);
  });

  test("usuario SÍ puede actualizar su propio perfil", async () => {
    const db = inspectorContext("user-a", "tenant-a").firestore();
    await assertSucceeds(
      db.collection("users").doc("user-a").update({
        displayName: "Juan Inspector",
        updatedAt: new Date(),
        updatedBy: "user-a",
      })
    );
  });

  test("usuario NO puede cambiar su propio rol", async () => {
    const db = inspectorContext("user-a", "tenant-a").firestore();
    await assertFails(
      db.collection("users").doc("user-a").update({
        role: "tenantadmin",  // ← Escalada de privilegios
        updatedAt: new Date(),
        updatedBy: "user-a",
      })
    );
  });

  test("usuario NO puede cambiar su tenantId", async () => {
    const db = inspectorContext("user-a", "tenant-a").firestore();
    await assertFails(
      db.collection("users").doc("user-a").update({
        tenantId: "tenant-b",  // ← Cross-tenant injection
        updatedAt: new Date(),
        updatedBy: "user-a",
      })
    );
  });
});
