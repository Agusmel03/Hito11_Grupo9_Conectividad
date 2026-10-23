const database = db.getSiblingDB("fixture2030");

print("=== COLECCIONES ===");
printjson(database.getCollectionNames());

print("=== CANTIDAD DE DOCUMENTOS ===");

for (const nombre of database.getCollectionNames()) {
    print(nombre + ": " + database.getCollection(nombre).countDocuments({}));
}

print("=== DOCUMENTO DE EJEMPLO ===");

for (const nombre of database.getCollectionNames()) {
    const documento = database.getCollection(nombre).findOne(
        {},
        { _id: 1 }
    );

    print(nombre + ":");
    printjson(documento);
}
